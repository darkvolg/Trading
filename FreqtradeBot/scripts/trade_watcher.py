#!/usr/bin/env python3
"""Trade Watcher - sends personal Telegram notification when new trades appear.

Monitors the Freqtrade SQLite database and sends a Telegram message
to the admin when new trades are opened or closed.

Usage:
    python trade_watcher.py

Environment:
    TG_TOKEN          - Telegram bot token (or from config.json)
    ADMIN_CHAT_ID     - Admin's personal chat ID for notifications
    FT_HOME           - Freqtrade base directory

Cron (every 5 min):
    */5 * * * * ADMIN_CHAT_ID=YOUR_ID /opt/freqtrade/venv/bin/python3 /opt/freqtrade/scripts/trade_watcher.py
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
FT_HOME = Path(os.environ.get("FT_HOME", SCRIPT_DIR.parent))
CONFIG_PATH = Path(os.environ.get("FT_CONFIG_PATH", FT_HOME / "config.json"))
STATE_FILE = FT_HOME / "user_data" / ".trade_watcher_state.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = FT_HOME / "user_data" / "logs" / "trade_watcher.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("trade_watcher")


# ═══════════════════════════════════════════════════════════════════════════
# Config & Credentials
# ═══════════════════════════════════════════════════════════════════════════

def load_config() -> dict[str, Any]:
    """Load Freqtrade config.json."""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Cannot read config: %s", exc)
        return {}


def get_telegram_credentials(config: dict[str, Any]) -> tuple[str, str]:
    """Return (token, chat_id) from env vars or config.json.

    chat_id prefers ADMIN_CHAT_ID env var (personal notifications),
    falls back to TELEGRAM_CHAT_ID / config telegram.chat_id.
    """
    token = (
        os.environ.get("TG_TOKEN")
        or os.environ.get("TELEGRAM_BOT_TOKEN")
        or config.get("telegram", {}).get("token", "")
    )
    chat_id = (
        os.environ.get("ADMIN_CHAT_ID")
        or os.environ.get("TELEGRAM_CHAT_ID")
        or os.environ.get("TG_CHAT_ID")
        or str(config.get("telegram", {}).get("chat_id", ""))
    )
    return token, chat_id


def is_dry_run(config: dict[str, Any]) -> bool:
    """Check if bot is in dry_run mode."""
    return config.get("dry_run", True)


def get_db_path(config: dict[str, Any]) -> Path:
    """Return path to the correct SQLite database."""
    db_url = config.get("db_url", "")
    if db_url.startswith("sqlite:///"):
        # Absolute or relative path after sqlite:///
        db_file = db_url.replace("sqlite:///", "")
        p = Path(db_file)
        if p.is_absolute():
            return p
        return FT_HOME / p

    # Default DB names
    if is_dry_run(config):
        return FT_HOME / "tradesv3.dryrun.sqlite"
    return FT_HOME / "tradesv3.sqlite"


# ═══════════════════════════════════════════════════════════════════════════
# State management
# ═══════════════════════════════════════════════════════════════════════════

def load_state() -> dict[str, Any]:
    """Load last notified trade ID from state file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_notified_trade_id": 0}


def save_state(state: dict[str, Any]) -> None:
    """Persist state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════════════════════════════

def fetch_new_trades(db_path: Path, last_id: int) -> list[dict[str, Any]]:
    """Query trades with id > last_id from the Freqtrade SQLite DB."""
    if not db_path.exists():
        logger.warning("Database not found: %s", db_path)
        return []

    trades = []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM trades WHERE id > ? ORDER BY id", (last_id,)
        )
        for row in cursor:
            trades.append(dict(row))
        conn.close()
    except sqlite3.Error as exc:
        logger.error("Database error: %s", exc)
    return trades


# ═══════════════════════════════════════════════════════════════════════════
# Telegram
# ═══════════════════════════════════════════════════════════════════════════

def send_telegram(token: str, chat_id: str, text: str) -> bool:
    """Send a message via Telegram Bot API. Returns True on success."""
    if not token or not chat_id:
        logger.error("Telegram credentials missing — cannot send notification.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            logger.info("Notification sent: %s", text[:80])
            return True
        logger.error("Telegram API error %s: %s", resp.status_code, resp.text[:200])
    except requests.RequestException as exc:
        logger.error("Telegram request failed: %s", exc)
    return False


# ═══════════════════════════════════════════════════════════════════════════
# Message formatting
# ═══════════════════════════════════════════════════════════════════════════

def format_trade_message(trade: dict[str, Any], dry_run: bool) -> str:
    """Format a trade notification message."""
    pair = trade.get("pair", "???")
    direction = trade.get("trade_direction", trade.get("is_short", False))
    if isinstance(direction, bool):
        direction = "SHORT" if direction else "LONG"
    elif isinstance(direction, int):
        direction = "SHORT" if direction else "LONG"
    else:
        direction = str(direction).upper() if direction else "LONG"

    open_date = trade.get("open_date", "")
    stake_amount = trade.get("stake_amount", 0)
    open_rate = trade.get("open_rate", 0)

    lines = [
        "\U0001f514 <b>New trade!</b>",
        "",
        f"<b>{pair}</b> {direction}",
        f"Opened: {open_date}",
        f"Amount: {stake_amount} USDT",
        f"Entry: {open_rate}",
    ]

    close_date = trade.get("close_date")
    if close_date:
        profit_ratio = trade.get("close_profit", trade.get("profit_ratio", 0)) or 0
        exit_reason = trade.get("exit_reason", trade.get("sell_reason", ""))
        profit_pct = profit_ratio * 100
        profit_emoji = "\U0001f7e2" if profit_ratio >= 0 else "\U0001f534"

        lines.append("")
        lines.append(f"Closed: {close_date}")
        lines.append(f"P&L: {profit_emoji} {profit_pct:+.2f}%")
        if exit_reason:
            lines.append(f"Reason: {exit_reason}")

    lines.append("")
    mode = "\U0001f7e2 DRY RUN" if dry_run else "\U0001f4b0 LIVE"
    lines.append(mode)

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    logger.info("Trade watcher started")

    config = load_config()
    token, chat_id = get_telegram_credentials(config)
    dry_run = is_dry_run(config)
    db_path = get_db_path(config)

    logger.info("Mode: %s | DB: %s", "dry_run" if dry_run else "LIVE", db_path)

    state = load_state()
    last_id = state.get("last_notified_trade_id", 0)

    new_trades = fetch_new_trades(db_path, last_id)

    if not new_trades:
        logger.info("No new trades since id=%d", last_id)
        return

    logger.info("Found %d new trade(s)", len(new_trades))

    max_id = last_id
    sent_count = 0

    for trade in new_trades:
        trade_id = trade.get("id", 0)
        msg = format_trade_message(trade, dry_run)
        if send_telegram(token, chat_id, msg):
            sent_count += 1
        max_id = max(max_id, trade_id)

    # Update state even if some sends failed — avoid duplicate spam
    state["last_notified_trade_id"] = max_id
    save_state(state)

    logger.info(
        "Done: %d/%d notifications sent, last_id=%d",
        sent_count, len(new_trades), max_id,
    )


if __name__ == "__main__":
    main()
