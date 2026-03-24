#!/usr/bin/env python3
"""
Delayed Signals — sends stripped-down signals to the FREE Telegram channel.

Reads queued signals from SQLite and sends them after a 3-hour delay.
Free channel gets a simplified version (no confidence, no indicators, no "why").

Run via cron every 15 minutes:
    */15 * * * * /usr/bin/python3 /path/to/scripts/delayed_signals.py
"""

import json
import logging
import os
import sqlite3
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# Allow importing from strategies directory
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "user_data", "strategies",
))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("delayed_signals")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FT_HOME = os.environ.get(
    "FT_HOME",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
DB_PATH = os.path.join(FT_HOME, "price_alerts.db")
CONFIG_PATH = os.path.join(FT_HOME, "config.json")

DELAY_HOURS = 3
TG_API = "https://api.telegram.org/bot{token}/sendMessage"

# Bybit affiliate (single source of truth: trendrider_config.py)
from trendrider_config import BYBIT_REFERRAL_LINK  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_tg_token() -> str:
    """Return Telegram bot token from env or Freqtrade config.json."""
    token = os.getenv("TG_TOKEN")
    if token:
        return token

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        token = cfg.get("telegram", {}).get("token", "")
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Cannot read config for TG_TOKEN: %s", exc)

    if not token:
        raise RuntimeError("TG_TOKEN is not set and not found in config.json")
    return token


def get_free_channel_id() -> str:
    """Return FREE_CHANNEL_ID from env (required)."""
    channel_id = os.getenv("FREE_CHANNEL_ID")
    if not channel_id:
        raise RuntimeError("FREE_CHANNEL_ID env variable is required")
    return channel_id


def send_telegram(token: str, chat_id: str, text: str) -> None:
    """Send a message via Telegram Bot API using urllib (no extra deps)."""
    url = TG_API.format(token=token)
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                body = resp.read().decode()
                logger.error("Telegram API error %d: %s", resp.status, body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else ""
        logger.error("Telegram HTTP error %d: %s", exc.code, body)
        raise
    except urllib.error.URLError as exc:
        logger.error("Telegram URL error: %s", exc.reason)
        raise


def format_signal(row: dict) -> str:
    """Build the stripped-down free-channel signal message."""
    return (
        f"TRENDRIDER SIGNAL #{row['signal_num']:03d}\n"
        f"════════════════════════════\n"
        f"{row['pair']} | {row['side']} | {row['leverage']}x\n"
        f"Setup: {row['setup_name']}\n"
        f"════════════════════════════\n"
        f"\n"
        f"Entry Zone: {row['entry_low']} - {row['entry_high']} USDT\n"
        f"Stop Loss: {row['sl_price']} ({row['sl_pct']}%)\n"
        f"\n"
        f"R:R = 1:{row['rr_ratio']}\n"
        f"\n"
        f"Exit: ROI targets + trailing stop\n"
        f"\n"
        f"Regime: {row['regime']}\n"
        f"════════════════════════════\n"
        f"📈 Trade on Bybit → {BYBIT_REFERRAL_LINK}\n"
        f"⏱ Signal delayed 3h | Real-time → @TrendRiderSignals\n"
        f"💎 Plans: /plans in @TrendRiderSignals\\_bot"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    if not os.path.exists(DB_PATH):
        logger.info("Database not found at %s — nothing to do", DB_PATH)
        return

    token = get_tg_token()
    channel_id = get_free_channel_id()

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=DELAY_HOURS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT * FROM signal_queue "
            "WHERE sent_free = 0 AND created_at <= ? "
            "ORDER BY created_at ASC",
            (cutoff,),
        )
        rows = cur.fetchall()

        if not rows:
            logger.info("No pending delayed signals")
            return

        sent = 0
        for row in rows:
            row_dict = dict(row)
            text = format_signal(row_dict)
            try:
                send_telegram(token, channel_id, text)
                conn.execute(
                    "UPDATE signal_queue SET sent_free = 1 WHERE id = ?",
                    (row_dict["id"],),
                )
                conn.commit()
                sent += 1
                logger.info(
                    "Sent delayed signal #%03d for %s to free channel",
                    row_dict["signal_num"],
                    row_dict["pair"],
                )
            except Exception:
                logger.exception(
                    "Failed to send signal #%03d for %s",
                    row_dict["signal_num"],
                    row_dict["pair"],
                )
                # Continue with next signal — don't break the batch
                continue

        logger.info("Done: %d/%d delayed signals sent", sent, len(rows))

    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc):
            logger.info("signal_queue table does not exist yet — nothing to do")
        else:
            raise
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)
