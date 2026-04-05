#!/usr/bin/env python3
"""
Friday Weekly Recap — sends 7-day trading performance to Telegram.
Run via cron: 0 18 * * 5 /usr/bin/python3 /path/to/scripts/friday_recap.py
"""

import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FT_HOME = os.environ.get(
    "FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))
DB_PATH = os.getenv("FT_DB_PATH", os.path.join(FT_HOME, "tradesv3.dryrun.sqlite"))

GOOGLE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1ZWRJ0PcBSk910MZv426PrleriBnInykr3OebWXJPm-g"
)


def get_telegram_config() -> tuple[str, str]:
    """Return (token, chat_id) from env vars or config.json."""
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if token and chat_id:
        return token, chat_id

    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        tg = cfg.get("telegram", {})
        return tg["token"], str(tg["chat_id"])
    except Exception as e:
        print(f"[ERROR] Cannot read Telegram config: {e}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def query_trades(db_path: str, days: int) -> list[dict]:
    """Return closed trades from the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT pair, close_profit, close_profit_abs, close_date
            FROM trades
            WHERE close_date >= ? AND is_open = 0
            ORDER BY close_date ASC
            """,
            (cutoff,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] DB query failed: {e}", file=sys.stderr)
        return []


def compute_stats(trades: list[dict]) -> dict:
    """Compute aggregate stats from a list of trade dicts."""
    total = len(trades)
    if total == 0:
        return {"total": 0}

    profits = [t["close_profit"] or 0.0 for t in trades]
    profits_abs = [t["close_profit_abs"] or 0.0 for t in trades]

    wins = sum(1 for p in profits if p > 0)
    losses = total - wins
    win_rate = (wins / total) * 100

    total_profit_pct = sum(profits) * 100  # close_profit is ratio (0.01 = 1%)
    avg_profit_pct = total_profit_pct / total
    total_profit_usd = sum(profits_abs)

    best_trade = max(trades, key=lambda t: t["close_profit"] or 0.0)
    worst_trade = min(trades, key=lambda t: t["close_profit"] or 0.0)

    # Per-pair breakdown
    by_pair: dict[str, dict] = defaultdict(lambda: {"count": 0, "profit_pct": 0.0})
    for t in trades:
        pair = t["pair"]
        by_pair[pair]["count"] += 1
        by_pair[pair]["profit_pct"] += (t["close_profit"] or 0.0) * 100

    # Sort pairs by trade count descending
    pair_stats = sorted(by_pair.items(), key=lambda x: x[1]["count"], reverse=True)

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_profit_pct": total_profit_pct,
        "avg_profit_pct": avg_profit_pct,
        "total_profit_usd": total_profit_usd,
        "best": best_trade,
        "worst": worst_trade,
        "pair_stats": pair_stats,
    }


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------

def _sign(val: float) -> str:
    return "+" if val >= 0 else ""


def format_date_range() -> str:
    """Return 'DD-DD Mon YYYY' for the last 7 days."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    if week_ago.month == now.month:
        return f"{week_ago.day}-{now.day} {now.strftime('%b %Y')}"
    return f"{week_ago.strftime('%-d %b')} - {now.strftime('%-d %b %Y')}"


def build_weekly_message(week: dict, running: dict) -> str:
    """Build the full recap message when there are weekly trades."""
    header = f"WEEKLY RECAP | {format_date_range()}"
    sep = "=" * 37

    lines = [header, sep, ""]

    # Performance
    lines.append("PERFORMANCE")
    lines.append(
        f"Trades: {week['total']} | Won: {week['wins']} | Lost: {week['losses']}"
    )
    lines.append(f"Win Rate: {week['win_rate']:.1f}%")
    lines.append(
        f"Total Profit: {_sign(week['total_profit_pct'])}{week['total_profit_pct']:.2f}%"
        f" (${week['total_profit_usd']:.2f})"
    )
    lines.append(f"Avg Trade: {_sign(week['avg_profit_pct'])}{week['avg_profit_pct']:.2f}%")
    lines.append("")

    # Highlights
    best = week["best"]
    worst = week["worst"]
    best_pct = (best["close_profit"] or 0) * 100
    worst_pct = (worst["close_profit"] or 0) * 100

    lines.append("HIGHLIGHTS")
    lines.append(f"Best: {best['pair']} {_sign(best_pct)}{best_pct:.2f}%")
    lines.append(f"Worst: {worst['pair']} {_sign(worst_pct)}{worst_pct:.2f}%")
    lines.append("")

    # By pair
    lines.append("BY PAIR")
    for pair, ps in week["pair_stats"]:
        t_word = "trade" if ps["count"] == 1 else "trades"
        pct = ps["profit_pct"]
        lines.append(
            f"{pair}: {ps['count']} {t_word:<6s} | {_sign(pct)}{pct:.2f}%"
        )
    lines.append("")

    # Running 30-day stats
    if running["total"] > 0:
        lines.append("RUNNING (30 DAYS)")
        lines.append(
            f"{running['wins']}W / {running['losses']}L"
            f" | {running['win_rate']:.1f}% WR"
            f" | {_sign(running['total_profit_pct'])}{running['total_profit_pct']:.2f}%"
        )
        lines.append("")

    lines.append(sep)
    lines.append(f"Full history: {GOOGLE_SHEET_URL}")
    lines.append("TrendRider AI | @TrendRiderSignals")

    return "\n".join(lines)


def build_quiet_message(running: dict) -> str:
    """Build message when no trades closed this week."""
    header = f"WEEKLY RECAP | {format_date_range()}"
    sep = "=" * 37

    lines = [header, sep, ""]
    lines.append("No trades closed this week — quiet week.")
    lines.append("")

    if running["total"] > 0:
        lines.append("RUNNING (30 DAYS)")
        lines.append(
            f"Trades: {running['total']} | Won: {running['wins']} | Lost: {running['losses']}"
        )
        lines.append(f"Win Rate: {running['win_rate']:.1f}%")
        lines.append(
            f"Total Profit: {_sign(running['total_profit_pct'])}{running['total_profit_pct']:.2f}%"
            f" (${running['total_profit_usd']:.2f})"
        )
        lines.append("")
    else:
        lines.append("No trades in the last 30 days either.")
        lines.append("")

    lines.append(sep)
    lines.append(f"Full history: {GOOGLE_SHEET_URL}")
    lines.append("TrendRider AI | @TrendRiderSignals")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=15)
    if not resp.ok:
        print(f"[ERROR] Telegram API: {resp.status_code} {resp.text}", file=sys.stderr)
    else:
        print("[OK] Weekly recap sent to Telegram.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    token, chat_id = get_telegram_config()

    week_trades = query_trades(DB_PATH, days=7)
    month_trades = query_trades(DB_PATH, days=30)

    week_stats = compute_stats(week_trades)
    running_stats = compute_stats(month_trades)

    if week_stats["total"] > 0:
        message = build_weekly_message(week_stats, running_stats)
    else:
        message = build_quiet_message(running_stats)

    send_telegram(token, chat_id, message)


if __name__ == "__main__":
    main()
