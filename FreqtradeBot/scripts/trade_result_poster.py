#!/usr/bin/env python3
"""
Trade Result Poster — posts beautiful trade result cards to the FREE Telegram channel.

Monitors the Freqtrade SQLite database for recently closed trades and posts
formatted result cards with P&L, duration, and running stats.

Entry signals go to the free channel (delayed via delayed_signals.py),
but results (P&L) are the most important marketing content.

Usage:
    python trade_result_poster.py

Environment:
    TG_TOKEN          - Telegram bot token (or from config.json)
    FREE_CHANNEL_ID   - Free public channel chat ID
    FT_HOME           - Freqtrade base directory

Cron (every 5 min):
    */5 * * * * FREE_CHANNEL_ID=YOUR_ID /opt/freqtrade/venv/bin/python3 /opt/freqtrade/scripts/trade_result_poster.py
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Allow importing from strategies directory
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
STRATEGIES_DIR = SCRIPT_DIR.parent / "user_data" / "strategies"
if str(STRATEGIES_DIR) not in sys.path:
    sys.path.insert(0, str(STRATEGIES_DIR))

from trendrider_config import (  # noqa: E402
    BYBIT_REFERRAL_LINK,
    SETUP_NAMES,
    EXIT_REASONS,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
FT_HOME = Path(os.environ.get("FT_HOME", SCRIPT_DIR.parent))
CONFIG_PATH = Path(os.environ.get("FT_CONFIG_PATH", FT_HOME / "config.json"))
STATE_FILE = FT_HOME / "user_data" / ".trade_result_poster_state.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = FT_HOME / "user_data" / "logs" / "trade_result_poster.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("trade_result_poster")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STATS_PERIOD_DAYS = 30
TG_API = "https://api.telegram.org/bot{token}/sendMessage"


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


def get_tg_token(config: dict[str, Any]) -> str:
    """Return Telegram bot token from env or config.json."""
    token = (
        os.environ.get("TG_TOKEN")
        or os.environ.get("TELEGRAM_BOT_TOKEN")
        or config.get("telegram", {}).get("token", "")
    )
    if not token:
        raise RuntimeError("TG_TOKEN is not set and not found in config.json")
    return token


def get_free_channel_id() -> str:
    """Return FREE_CHANNEL_ID from env (required)."""
    channel_id = os.environ.get("FREE_CHANNEL_ID")
    if not channel_id:
        raise RuntimeError("FREE_CHANNEL_ID env variable is required")
    return channel_id


def is_dry_run(config: dict[str, Any]) -> bool:
    """Check if bot is in dry_run mode."""
    return config.get("dry_run", True)


def get_db_path(config: dict[str, Any]) -> Path:
    """Return path to the correct SQLite database."""
    db_url = config.get("db_url", "")
    if db_url.startswith("sqlite:///"):
        db_file = db_url.replace("sqlite:///", "")
        p = Path(db_file)
        if p.is_absolute():
            return p
        return FT_HOME / p

    if is_dry_run(config):
        return FT_HOME / "tradesv3.dryrun.sqlite"
    return FT_HOME / "tradesv3.sqlite"


# ═══════════════════════════════════════════════════════════════════════════
# State management
# ═══════════════════════════════════════════════════════════════════════════

def load_state() -> dict[str, Any]:
    """Load state with last posted trade ID and trade counter."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_posted_trade_id": 0, "trade_counter": 0}


def save_state(state: dict[str, Any]) -> None:
    """Persist state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════════════════════════════

def fetch_closed_trades(db_path: Path, last_id: int) -> list[dict[str, Any]]:
    """Query recently closed trades with id > last_id."""
    if not db_path.exists():
        logger.warning("Database not found: %s", db_path)
        return []

    trades: list[dict[str, Any]] = []
    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT id, pair, is_short, open_date, close_date,
                   stake_amount, open_rate, close_rate, close_profit,
                   close_profit_abs, exit_reason, enter_tag,
                   leverage, is_open
            FROM trades
            WHERE id > ? AND is_open = 0 AND close_date IS NOT NULL
            ORDER BY id
            """,
            (last_id,),
        )
        for row in cursor:
            trades.append(dict(row))
        conn.close()
    except sqlite3.Error as exc:
        logger.error("Database error: %s", exc)
    return trades


def fetch_running_stats(db_path: Path) -> dict[str, Any]:
    """Fetch running statistics for the last 30 days from the trade DB."""
    stats: dict[str, Any] = {
        "wins": 0,
        "losses": 0,
        "total_profit_pct": 0.0,
        "win_rate": 0.0,
        "total_trades": 0,
    }
    if not db_path.exists():
        return stats

    since = (datetime.now(timezone.utc) - timedelta(days=STATS_PERIOD_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT close_profit
            FROM trades
            WHERE is_open = 0 AND close_date IS NOT NULL AND close_date >= ?
            ORDER BY close_date DESC
            """,
            (since,),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return stats

        wins = sum(1 for r in rows if (r["close_profit"] or 0) > 0)
        losses = len(rows) - wins
        total_profit_pct = sum((r["close_profit"] or 0) * 100 for r in rows)

        stats["wins"] = wins
        stats["losses"] = losses
        stats["total_trades"] = len(rows)
        stats["win_rate"] = (wins / len(rows)) * 100 if rows else 0
        stats["total_profit_pct"] = total_profit_pct

    except sqlite3.Error as exc:
        logger.error("Stats query error: %s", exc)

    return stats


# ═══════════════════════════════════════════════════════════════════════════
# Message formatting
# ═══════════════════════════════════════════════════════════════════════════

def format_duration(open_date_str: str, close_date_str: str) -> str:
    """Format trade duration as human-readable string."""
    try:
        # Handle both with and without timezone info
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                open_dt = datetime.strptime(open_date_str.split("+")[0].strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return "N/A"

        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                close_dt = datetime.strptime(close_date_str.split("+")[0].strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return "N/A"

        delta = close_dt - open_dt
        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            return "N/A"

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "N/A"


def get_direction(trade: dict[str, Any]) -> str:
    """Determine trade direction string."""
    # Check trade_direction first (e.g. from API / signal data)
    trade_dir = trade.get("trade_direction")
    if isinstance(trade_dir, str) and trade_dir:
        return trade_dir.upper()

    # Fallback to is_short flag (from SQLite)
    direction = trade.get("is_short", False)
    if isinstance(direction, bool):
        return "SHORT" if direction else "LONG"
    if isinstance(direction, int):
        return "SHORT" if direction else "LONG"
    if isinstance(direction, str) and direction:
        return direction.upper()
    return "LONG"


def format_price(price: float | None) -> str:
    """Format a price value with appropriate precision."""
    if price is None or price == 0:
        return "N/A"
    if price >= 1000:
        return f"${price:,.2f}"
    if price >= 1:
        return f"${price:.4f}"
    return f"${price:.6f}"


def format_trade_result(
    trade: dict[str, Any],
    trade_number: int,
    stats: dict[str, Any],
) -> str:
    """Format a beautiful trade result card for the free channel.

    Args:
        trade: Trade data dict from SQLite.
        trade_number: Sequential trade result number.
        stats: Running stats dict from fetch_running_stats().

    Returns:
        Formatted Telegram message string (Markdown parse_mode).
    """
    pair = trade.get("pair", "???")
    direction = get_direction(trade)
    direction_emoji = "\U0001f7e2" if direction == "LONG" else "\U0001f534"

    open_rate = trade.get("open_rate", 0)
    close_rate = trade.get("close_rate", 0)
    profit_ratio = trade.get("close_profit", 0) or 0
    profit_pct = profit_ratio * 100
    leverage = trade.get("leverage", 1) or 1

    # P&L emoji
    if profit_pct > 0:
        pnl_emoji = "\u2705"
        pnl_prefix = "+"
    else:
        pnl_emoji = "\u274c"
        pnl_prefix = ""

    # Duration
    open_date = trade.get("open_date", "")
    close_date = trade.get("close_date", "")
    duration = format_duration(str(open_date), str(close_date))

    # Exit reason
    exit_reason_raw = trade.get("exit_reason") or trade.get("sell_reason") or ""
    exit_reason = EXIT_REASONS.get(exit_reason_raw, exit_reason_raw)

    # Setup name from enter_tag
    enter_tag = trade.get("enter_tag") or ""
    setup_name = SETUP_NAMES.get(enter_tag, enter_tag or "")

    # Leverage display
    lev_str = f" | {leverage}x" if leverage and leverage > 1 else ""

    # Build message
    sep = "\u2501" * 17

    lines = [
        f"\U0001f4ca *Trade Result #{trade_number:03d}*",
        "",
        f"{direction_emoji} *{direction}* {pair}{lev_str}",
        sep,
        f"\U0001f4c8 Entry: `{format_price(open_rate)}`",
        f"\U0001f4c9 Exit:  `{format_price(close_rate)}`",
        f"\U0001f4b0 P&L: *{pnl_prefix}{profit_pct:.2f}%* {pnl_emoji}",
        f"\u23f1 Duration: {duration}",
    ]

    if exit_reason:
        lines.append(f"\U0001f3af Reason: {exit_reason}")

    if setup_name:
        lines.append(f"\U0001f527 Setup: {setup_name}")

    lines.append(sep)

    # Running stats
    if stats.get("total_trades", 0) > 0:
        wr = stats["win_rate"]
        w = stats["wins"]
        losses = stats["losses"]
        tp = stats["total_profit_pct"]
        tp_prefix = "+" if tp >= 0 else ""

        lines.append("")
        lines.append(
            f"\U0001f4ca *Running Stats ({STATS_PERIOD_DAYS}d):*"
        )
        lines.append(
            f"\U0001f3c6 Win Rate: {wr:.1f}% | \U0001f4c8 {w}W / {losses}L"
        )
        lines.append(
            f"\U0001f4b0 Total: {tp_prefix}{tp:.1f}%"
        )
        lines.append("")
        lines.append(sep)

    # CTA footer
    lines.append("")
    lines.append("\U0001f680 Get real-time signals first!")
    lines.append("\U0001f449 @TrendRiderSignals")
    lines.append(f"\U0001f4c8 [Trade on Bybit]({BYBIT_REFERRAL_LINK})")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Telegram
# ═══════════════════════════════════════════════════════════════════════════

def send_telegram(token: str, chat_id: str, text: str) -> bool:
    """Send a message via Telegram Bot API. Returns True on success."""
    if not token or not chat_id:
        logger.error("Telegram credentials missing — cannot send.")
        return False

    url = TG_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            logger.info("Result card sent to channel: %s", text[:80])
            return True
        logger.error("Telegram API error %s: %s", resp.status_code, resp.text[:200])
    except requests.RequestException as exc:
        logger.error("Telegram request failed: %s", exc)
    return False


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    logger.info("Trade result poster started")

    config = load_config()
    token = get_tg_token(config)
    channel_id = get_free_channel_id()
    db_path = get_db_path(config)
    dry_run = is_dry_run(config)

    logger.info("Mode: %s | DB: %s", "dry_run" if dry_run else "LIVE", db_path)

    state = load_state()
    last_id = state.get("last_posted_trade_id", 0)
    trade_counter = state.get("trade_counter", 0)

    closed_trades = fetch_closed_trades(db_path, last_id)

    if not closed_trades:
        logger.info("No new closed trades since id=%d", last_id)
        return

    logger.info("Found %d new closed trade(s)", len(closed_trades))

    # Fetch running stats once (shared across all cards)
    stats = fetch_running_stats(db_path)

    max_id = last_id
    sent_count = 0

    for trade in closed_trades:
        trade_id = trade.get("id", 0)
        trade_counter += 1

        msg = format_trade_result(trade, trade_counter, stats)
        if send_telegram(token, channel_id, msg):
            sent_count += 1
        max_id = max(max_id, trade_id)

    # Update state even if some sends failed — avoid duplicate spam
    state["last_posted_trade_id"] = max_id
    state["trade_counter"] = trade_counter
    save_state(state)

    logger.info(
        "Done: %d/%d result cards sent, last_id=%d, counter=%d",
        sent_count, len(closed_trades), max_id, trade_counter,
    )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)
