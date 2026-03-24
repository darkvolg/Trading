#!/usr/bin/env python3
"""
TrendRider Health Monitor — cron-friendly watchdog for Freqtrade.

Checks:
  1. Freqtrade API reachability (ping endpoint)
  2. Bot state (running / stopped / error)
  3. Recent log errors (last 500 lines)
  4. Trade activity (no trades in 24h warning)
  5. Drawdown anomaly (> threshold)

Sends Telegram alerts when something is wrong. Deduplicates alerts so the
same issue is not reported more than once per ALERT_COOLDOWN_SECONDS.

Usage (cron every 5 min):
  */5 * * * * /usr/bin/python3 /opt/freqtrade/scripts/health_monitor.py

Systemd timer alternative — create two files:

  # /etc/systemd/system/trendrider-health.service
  [Unit]
  Description=TrendRider Health Monitor
  After=network.target
  [Service]
  Type=oneshot
  ExecStart=/usr/bin/python3 /opt/freqtrade/scripts/health_monitor.py
  Environment=FT_HOME=/opt/freqtrade
  Environment=TELEGRAM_BOT_TOKEN=your-token
  Environment=TELEGRAM_CHAT_ID=your-chat-id

  # /etc/systemd/system/trendrider-health.timer
  [Unit]
  Description=Run TrendRider Health Monitor every 5 minutes
  [Timer]
  OnBootSec=60
  OnUnitActiveSec=300
  [Install]
  WantedBy=timers.target

  $ systemctl daemon-reload && systemctl enable --now trendrider-health.timer

Environment variables:
  TELEGRAM_BOT_TOKEN  — Telegram bot token (falls back to config.json)
  TELEGRAM_CHAT_ID    — Telegram chat id   (falls back to config.json)
  FREQTRADE_API_URL   — API base URL (default: http://127.0.0.1:8081)
  FREQTRADE_API_USER  — API username (default: freqtrader)
  FREQTRADE_API_PASS  — API password (required for authenticated endpoints)
  FT_HOME             — Freqtrade home directory
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
FT_HOME = Path(os.environ.get("FT_HOME", SCRIPT_DIR.parent))
CONFIG_PATH = Path(os.environ.get("FT_CONFIG_PATH", FT_HOME / "config.json"))
LOG_DIR = FT_HOME / "user_data" / "logs"
STATE_FILE = FT_HOME / "user_data" / ".health_state.json"

# ---------------------------------------------------------------------------
# Thresholds — edit to taste
# ---------------------------------------------------------------------------
ALERT_COOLDOWN_SECONDS = 3600          # 1 hour — same alert not repeated sooner
NO_TRADE_HOURS = 24                    # warn if no trades for this long
MAX_DRAWDOWN_PCT = 20.0                # warn if drawdown exceeds this %
LOG_ERROR_SCAN_LINES = 500             # how many tail lines to scan
API_TIMEOUT_SECONDS = 10               # HTTP timeout for Freqtrade API

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = FT_HOME / "user_data" / "logs" / "health_monitor.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("health_monitor")


# ═══════════════════════════════════════════════════════════════════════════
# Credentials
# ═══════════════════════════════════════════════════════════════════════════

def get_telegram_credentials() -> tuple[str, str]:
    """Return (token, chat_id) from env vars or Freqtrade config.json."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TG_CHAT_ID")
    if token and chat_id:
        return token, chat_id

    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            cfg = json.load(fh)
        tg = cfg.get("telegram", {})
        token = token or tg.get("token", "")
        chat_id = chat_id or str(tg.get("chat_id", ""))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Cannot read config for TG credentials: %s", exc)

    return token or "", chat_id or ""


def get_api_url() -> str:
    return os.environ.get("FREQTRADE_API_URL", "http://127.0.0.1:8081")


def get_api_auth() -> tuple[str, str] | None:
    user = os.environ.get("FREQTRADE_API_USER", "freqtrader")
    password = os.environ.get("FREQTRADE_API_PASS", "")
    if password:
        return (user, password)
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Alert state  (deduplication)
# ═══════════════════════════════════════════════════════════════════════════

def _load_state() -> dict[str, Any]:
    """Load persisted alert timestamps."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh)


def _should_alert(state: dict[str, Any], key: str) -> bool:
    """Return True if enough time has passed since the last alert for *key*."""
    last = state.get(key, 0)
    return (time.time() - last) >= ALERT_COOLDOWN_SECONDS


def _mark_alerted(state: dict[str, Any], key: str) -> None:
    state[key] = time.time()


# ═══════════════════════════════════════════════════════════════════════════
# Telegram
# ═══════════════════════════════════════════════════════════════════════════

def send_telegram_alert(token: str, chat_id: str, text: str) -> bool:
    """Send a message via Telegram Bot API. Returns True on success."""
    if not token or not chat_id:
        logger.error("Telegram credentials missing — cannot send alert.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            logger.info("Alert sent: %s", text[:80])
            return True
        logger.error("Telegram API error %s: %s", resp.status_code, resp.text[:200])
    except requests.RequestException as exc:
        logger.error("Telegram request failed: %s", exc)
    return False


# ═══════════════════════════════════════════════════════════════════════════
# Health checks
# ═══════════════════════════════════════════════════════════════════════════

def check_api_ping(api_url: str, auth: tuple[str, str] | None) -> tuple[bool, str]:
    """Ping Freqtrade API. Returns (ok, detail)."""
    for endpoint in ("/api/v1/ping", "/api/v1/health"):
        url = f"{api_url}{endpoint}"
        try:
            resp = requests.get(url, auth=auth, timeout=API_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                return True, f"API OK ({endpoint})"
        except requests.RequestException:
            continue
    return False, "Freqtrade API unreachable"


def check_bot_state(api_url: str, auth: tuple[str, str] | None) -> tuple[bool, str]:
    """Check /api/v1/show_config or /api/v1/status for bot state."""
    try:
        resp = requests.get(
            f"{api_url}/api/v1/show_config", auth=auth, timeout=API_TIMEOUT_SECONDS
        )
        if resp.status_code == 200:
            data = resp.json()
            state = data.get("state", "unknown")
            if state == "running":
                return True, "Bot is running"
            return False, f"Bot state: {state}"
    except requests.RequestException as exc:
        return False, f"Cannot fetch bot state: {exc}"
    return False, "Cannot determine bot state"


def check_recent_trades(api_url: str, auth: tuple[str, str] | None) -> tuple[bool, str]:
    """Warn if there have been no trades opened in the last NO_TRADE_HOURS."""
    try:
        resp = requests.get(
            f"{api_url}/api/v1/status", auth=auth, timeout=API_TIMEOUT_SECONDS
        )
        if resp.status_code == 200:
            trades = resp.json()
            if trades:
                return True, f"{len(trades)} open trade(s)"

        # Check closed trades via /trades endpoint
        resp2 = requests.get(
            f"{api_url}/api/v1/trades",
            auth=auth,
            params={"limit": 5},
            timeout=API_TIMEOUT_SECONDS,
        )
        if resp2.status_code == 200:
            data = resp2.json()
            trade_list = data.get("trades", [])
            if trade_list:
                # Check the most recent trade open date
                latest = trade_list[0]
                open_date_str = latest.get("open_date", "")
                if open_date_str:
                    open_dt = datetime.fromisoformat(
                        open_date_str.replace("Z", "+00:00")
                    )
                    age = datetime.now(timezone.utc) - open_dt
                    if age > timedelta(hours=NO_TRADE_HOURS):
                        return (
                            False,
                            f"No new trades in {age.total_seconds() / 3600:.0f}h"
                            f" (threshold: {NO_TRADE_HOURS}h)",
                        )
                    return True, f"Last trade {age.total_seconds() / 3600:.1f}h ago"
            return False, f"No trades found in last {NO_TRADE_HOURS}h"
    except requests.RequestException as exc:
        return True, f"Could not check trades: {exc}"  # non-critical
    return True, "Trade check skipped"


def check_drawdown(api_url: str, auth: tuple[str, str] | None) -> tuple[bool, str]:
    """Check profit endpoint for unusual drawdown."""
    try:
        resp = requests.get(
            f"{api_url}/api/v1/profit", auth=auth, timeout=API_TIMEOUT_SECONDS
        )
        if resp.status_code == 200:
            data = resp.json()
            # Freqtrade reports profit_all_coin, profit_all_percent, etc.
            profit_pct = data.get("profit_all_percent", 0) or 0
            if profit_pct < -MAX_DRAWDOWN_PCT:
                return (
                    False,
                    f"Drawdown alert: {profit_pct:.1f}% (threshold: -{MAX_DRAWDOWN_PCT}%)",
                )
            return True, f"P&L: {profit_pct:+.1f}%"
    except requests.RequestException as exc:
        return True, f"Could not check drawdown: {exc}"
    return True, "Drawdown check skipped"


def check_log_errors() -> tuple[bool, str]:
    """Scan the latest Freqtrade log file for recent ERROR lines."""
    if not LOG_DIR.is_dir():
        return True, "Log directory not found — skipping"

    log_files = sorted(LOG_DIR.glob("freqtrade*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not log_files:
        return True, "No log files found — skipping"

    latest_log = log_files[0]
    try:
        with open(latest_log, encoding="utf-8", errors="replace") as fh:
            tail = deque(fh, maxlen=LOG_ERROR_SCAN_LINES)
    except OSError as exc:
        return True, f"Cannot read log: {exc}"

    error_pattern = re.compile(r"\bERROR\b")
    recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    errors: list[str] = []

    for line in tail:
        if error_pattern.search(line):
            # Try to parse timestamp (Freqtrade format: 2024-01-15 12:30:45,123)
            ts_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
            if ts_match:
                try:
                    ts = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S")
                    ts = ts.replace(tzinfo=timezone.utc)
                    if ts < recent_cutoff:
                        continue
                except ValueError:
                    pass
            errors.append(line.strip()[:120])

    if errors:
        sample = errors[-3:]  # last 3 errors
        return False, f"{len(errors)} recent errors. Latest:\n" + "\n".join(sample)
    return True, "No recent errors in logs"


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def run_health_checks() -> list[tuple[str, bool, str]]:
    """Run all checks and return [(name, ok, detail), ...]."""
    api_url = get_api_url()
    auth = get_api_auth()

    results = []
    results.append(("API Ping", *check_api_ping(api_url, auth)))
    results.append(("Bot State", *check_bot_state(api_url, auth)))
    results.append(("Trade Activity", *check_recent_trades(api_url, auth)))
    results.append(("Drawdown", *check_drawdown(api_url, auth)))
    results.append(("Log Errors", *check_log_errors()))
    return results


def main() -> None:
    logger.info("Health check started")
    token, chat_id = get_telegram_credentials()
    state = _load_state()
    results = run_health_checks()

    failures = [(name, detail) for name, ok, detail in results if not ok]

    for name, ok, detail in results:
        level = "OK" if ok else "FAIL"
        logger.info("  [%s] %s — %s", level, name, detail)

    if not failures:
        logger.info("All checks passed.")
        # Clear stale alert keys so next failure fires immediately
        if state:
            _save_state({})
        return

    # Build alert message
    lines = ["\u26a0\ufe0f *TrendRider Health Alert*\n"]
    alert_keys_fired: list[str] = []

    for name, detail in failures:
        key = f"alert_{name}"
        if _should_alert(state, key):
            lines.append(f"\u274c *{name}*: {detail}")
            _mark_alerted(state, key)
            alert_keys_fired.append(key)

    if len(lines) == 1:
        # All failures are still in cooldown
        logger.info("Failures detected but alerts are in cooldown.")
        _save_state(state)
        return

    lines.append(f"\n_Checked at {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC_")
    message = "\n".join(lines)

    sent = send_telegram_alert(token, chat_id, message)
    if not sent:
        logger.error("Failed to send Telegram alert!")

    _save_state(state)
    logger.info("Health check complete — %d issue(s) reported.", len(alert_keys_fired))


if __name__ == "__main__":
    main()
