#!/usr/bin/env python3
"""
Monthly Performance Report — sends previous month's trading stats to Telegram.
Run via cron: 0 10 1 * * /usr/bin/python3 /path/to/scripts/monthly_report.py
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

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
# Date helpers
# ---------------------------------------------------------------------------

def get_previous_month(today: datetime) -> tuple[datetime, datetime, str, int]:
    """Return (start, end, month_name, year) for the previous month."""
    first_of_current = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # End of previous month = first of current month
    end = first_of_current
    # Start of previous month
    if today.month == 1:
        start = first_of_current.replace(year=today.year - 1, month=12)
    else:
        start = first_of_current.replace(month=today.month - 1)
    month_name = start.strftime("%B")
    year = start.year
    return start, end, month_name, year


def parse_month_arg(month_str: str) -> tuple[datetime, datetime, str, int]:
    """Parse YYYY-MM and return (start, end, month_name, year)."""
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        print(f"[ERROR] Invalid month format: {month_str}. Use YYYY-MM.", file=sys.stderr)
        sys.exit(1)
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0,
                       tzinfo=timezone.utc)
    if dt.month == 12:
        end = start.replace(year=dt.year + 1, month=1)
    else:
        end = start.replace(month=dt.month + 1)
    return start, end, start.strftime("%B"), start.year


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def query_trades(db_path: str, start: datetime, end: datetime) -> list[dict]:
    """Return closed trades within [start, end) date range."""
    start_str = start.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end.strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT pair, close_profit AS profit_ratio, close_profit_abs, close_date,
                   open_date, stake_amount, exit_reason
            FROM trades
            WHERE is_open = 0 AND close_date >= ? AND close_date < ?
            ORDER BY close_date
            """,
            (start_str, end_str),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] DB query failed: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Stats calculation
# ---------------------------------------------------------------------------

def compute_stats(trades: list[dict]) -> dict:
    """Compute monthly aggregate stats from trade dicts."""
    total = len(trades)
    if total == 0:
        return {"total": 0}

    profits = [t["profit_ratio"] or 0.0 for t in trades]
    profits_abs = [t["close_profit_abs"] or 0.0 for t in trades]

    wins = sum(1 for p in profits if p > 0)
    losses = total - wins
    win_rate = (wins / total) * 100

    pnl_pct = sum(profits) * 100
    pnl_usd = sum(profits_abs)

    best_trade = max(trades, key=lambda t: t["profit_ratio"] or 0.0)
    worst_trade = min(trades, key=lambda t: t["profit_ratio"] or 0.0)

    # Average trade duration
    durations = []
    for t in trades:
        try:
            open_dt = datetime.fromisoformat(t["open_date"].replace(" ", "T"))
            close_dt = datetime.fromisoformat(t["close_date"].replace(" ", "T"))
            durations.append((close_dt - open_dt).total_seconds())
        except (ValueError, TypeError, AttributeError):
            pass

    avg_duration_secs = sum(durations) / len(durations) if durations else 0

    # By-pair breakdown
    by_pair: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "wins": 0, "profit_pct": 0.0}
    )
    for t in trades:
        pair = t["pair"]
        by_pair[pair]["count"] += 1
        ratio = t["profit_ratio"] or 0.0
        if ratio > 0:
            by_pair[pair]["wins"] += 1
        by_pair[pair]["profit_pct"] += ratio * 100

    pair_stats = sorted(by_pair.items(), key=lambda x: x[1]["count"], reverse=True)

    # Winning/losing streaks
    win_streak, loss_streak = compute_streaks(profits)

    # Average trades per week
    if len(trades) >= 2:
        try:
            first_close = datetime.fromisoformat(
                trades[0]["close_date"].replace(" ", "T")
            )
            last_close = datetime.fromisoformat(
                trades[-1]["close_date"].replace(" ", "T")
            )
            span_days = max((last_close - first_close).total_seconds() / 86400, 1)
            trades_per_week = total / (span_days / 7)
        except (ValueError, TypeError, AttributeError):
            trades_per_week = total / 4.0
    else:
        trades_per_week = total / 4.0

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "pnl_pct": pnl_pct,
        "pnl_usd": pnl_usd,
        "best": best_trade,
        "worst": worst_trade,
        "avg_duration_secs": avg_duration_secs,
        "pair_stats": pair_stats,
        "win_streak": win_streak,
        "loss_streak": loss_streak,
        "trades_per_week": trades_per_week,
    }


def compute_streaks(profits: list[float]) -> tuple[int, int]:
    """Return (longest_win_streak, longest_loss_streak)."""
    max_win = 0
    max_loss = 0
    cur_win = 0
    cur_loss = 0
    for p in profits:
        if p > 0:
            cur_win += 1
            cur_loss = 0
            max_win = max(max_win, cur_win)
        else:
            cur_loss += 1
            cur_win = 0
            max_loss = max(max_loss, cur_loss)
    return max_win, max_loss


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration string."""
    if seconds <= 0:
        return "N/A"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours >= 24:
        days = hours // 24
        rem_hours = hours % 24
        return f"{days}d {rem_hours}h"
    return f"{hours}h {minutes}m"


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------

def build_monthly_message(stats: dict, month_name: str, year: int) -> str:
    """Build the full monthly report message."""
    best = stats["best"]
    worst = stats["worst"]
    best_pct = (best["profit_ratio"] or 0) * 100
    worst_pct = (worst["profit_ratio"] or 0) * 100

    try:
        best_date = datetime.fromisoformat(
            best["close_date"].replace(" ", "T")
        ).strftime("%d %b")
    except (ValueError, TypeError, AttributeError):
        best_date = "N/A"

    try:
        worst_date = datetime.fromisoformat(
            worst["close_date"].replace(" ", "T")
        ).strftime("%d %b")
    except (ValueError, TypeError, AttributeError):
        worst_date = "N/A"

    avg_dur = format_duration(stats["avg_duration_secs"])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Pair table
    pair_lines = []
    for pair, ps in stats["pair_stats"]:
        avg_pct = ps["profit_pct"] / ps["count"] if ps["count"] > 0 else 0
        pair_lines.append(
            f"  {pair}: {ps['count']}t ({ps['wins']}W) "
            f"| {ps['profit_pct']:+.1f}% (avg {avg_pct:+.1f}%)"
        )
    pair_table = "\n".join(pair_lines) if pair_lines else "  No pairs"

    lines = [
        "\U0001f4c8 *TrendRider \u2014 Monthly Report*",
        f"_{month_name} {year}_",
        "",
        "\U0001f4ca *Performance*",
        f"Trades: {stats['total']} ({stats['wins']}W / {stats['losses']}L)",
        f"Win Rate: {stats['win_rate']:.1f}%",
        f"Total P&L: {stats['pnl_usd']:+.2f} USDT ({stats['pnl_pct']:+.1f}%)",
        f"Best: {best['pair']} {best_pct:+.1f}% ({best_date})",
        f"Worst: {worst['pair']} {worst_pct:+.1f}% ({worst_date})",
        f"Avg Duration: {avg_dur}",
        "",
        "\U0001f4cb *By Pair*",
        pair_table,
        "",
        "\U0001f4c8 *Streaks*",
        f"Win streak: {stats['win_streak']}",
        f"Loss streak: {stats['loss_streak']}",
        "",
        f"\U0001f517 [Full Trade History]({GOOGLE_SHEET_URL})",
        "",
        f"_Generated automatically on {today}_",
    ]
    return "\n".join(lines)


def build_no_trades_message(month_name: str, year: int) -> str:
    """Build message when no trades closed in the month."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "\U0001f4c8 *TrendRider \u2014 Monthly Report*",
        f"_{month_name} {year}_",
        "",
        "No trades closed this month.",
        "",
        f"\U0001f517 [Full Trade History]({GOOGLE_SHEET_URL})",
        "",
        f"_Generated automatically on {today}_",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Telegram (urllib-based)
# ---------------------------------------------------------------------------

def send_telegram(text: str) -> None:
    """Send a Markdown message to Telegram using urllib."""
    token, chat_id = get_telegram_config()

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                print("[OK] Monthly report sent to Telegram.")
            else:
                print(f"[WARN] Telegram API returned status {resp.status}.")
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Telegram HTTP error {e.code}: {e.reason}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"[ERROR] Telegram URL error: {e.reason}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Monthly trading performance report")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the report to stdout without sending to Telegram",
    )
    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help="Generate report for a specific month (YYYY-MM). Default: previous month.",
    )
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    # Determine date range
    if args.month:
        start, end, month_name, year = parse_month_arg(args.month)
    else:
        today = datetime.now(timezone.utc)
        start, end, month_name, year = get_previous_month(today)

    print(f"Generating report for {month_name} {year} "
          f"({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')})")

    trades = query_trades(DB_PATH, start, end)
    stats = compute_stats(trades)

    if stats["total"] > 0:
        message = build_monthly_message(stats, month_name, year)
    else:
        message = build_no_trades_message(month_name, year)

    if args.dry_run:
        print("\n--- DRY RUN ---")
        print(message)
        print("--- END ---\n")
    else:
        send_telegram(message)


if __name__ == "__main__":
    main()
