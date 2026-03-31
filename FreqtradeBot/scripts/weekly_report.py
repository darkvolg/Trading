#!/usr/bin/env python3
"""
TrendRider Weekly Report — generates weekly stats + equity chart and posts to Telegram.

Designed to run via cron every Sunday at 18:00 UTC:
    0 18 * * 0 /opt/freqtrade/venv/bin/python3 /opt/freqtrade/scripts/weekly_report.py

Flags:
    --dry-run       Save PNG locally, don't send to Telegram
    --save PATH     Save PNG to specified path
    --weeks-ago N   Generate report for N weeks ago (default: 0 = current week)

Environment:
    FREE_CHANNEL_ID   - Telegram channel ID for posting
    TG_TOKEN          - Telegram bot token (fallback: SUB_BOT_TOKEN, then config.json)
    FT_DB_PATH        - Path to Freqtrade SQLite database
    FT_HOME           - Freqtrade base directory (auto-detected if not set)
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.ticker as mticker
except ImportError as e:
    print(f"weekly_report.py: matplotlib not installed: {e}", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths & Logging
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
FT_HOME = Path(os.environ.get("FT_HOME", SCRIPT_DIR.parent))
CONFIG_PATH = Path(os.environ.get("FT_CONFIG_PATH", FT_HOME / "config.json"))
DB_PATH = os.environ.get("FT_DB_PATH", str(FT_HOME / "tradesv3.dryrun.sqlite"))

LOG_FILE = FT_HOME / "user_data" / "logs" / "weekly_report.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("weekly_report")

# ---------------------------------------------------------------------------
# Visual style (matches equity_curve.py branding)
# ---------------------------------------------------------------------------
BG_COLOR = "#1a1a2e"
GRID_COLOR = "#16213e"
EQUITY_COLOR = "#00d26a"
EQUITY_FILL_ALPHA = 0.18
TEXT_COLOR = "#e0e0e0"
ACCENT_COLOR = "#00d26a"
WATERMARK = "@TrendRiderSignals"
NEGATIVE_COLOR = "#ff6b6b"


# ---------------------------------------------------------------------------
# Telegram helpers (stdlib-only, same pattern as equity_curve.py)
# ---------------------------------------------------------------------------
def get_telegram_config() -> tuple[str, str]:
    """Return (token, channel_id) from env vars or config.json."""
    token = (
        os.environ.get("TG_TOKEN")
        or os.environ.get("SUB_BOT_TOKEN")
    )
    channel_id = os.environ.get("FREE_CHANNEL_ID")

    if not token:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            token = cfg.get("telegram", {}).get("token", "")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    if not channel_id:
        channel_id = os.environ.get("TG_CHAT_ID", "")

    return token or "", channel_id or ""


def send_photo(token: str, chat_id: str, photo_bytes: bytes, caption: str) -> dict:
    """Send a photo to Telegram via multipart/form-data using stdlib only."""
    boundary = "----FormBoundary" + os.urandom(8).hex()
    body = bytearray()

    for name, value in [("chat_id", chat_id), ("caption", caption), ("parse_mode", "HTML")]:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())

    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        'Content-Disposition: form-data; name="photo"; filename="weekly_report.png"\r\n'.encode()
    )
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(photo_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    req = Request(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def send_text(token: str, chat_id: str, text: str) -> dict:
    """Send a plain text message to Telegram."""
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Database queries
# ---------------------------------------------------------------------------
def fetch_weekly_trades(db_path: str, week_start: datetime, week_end: datetime) -> list[dict[str, Any]]:
    """Fetch all trades closed within the given week."""
    if not os.path.exists(db_path):
        logger.error("Database not found: %s", db_path)
        return []

    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, pair, open_date, close_date, open_rate, close_rate,
                   close_profit_abs, close_profit AS profit_ratio,
                   stake_amount, is_open
            FROM trades
            WHERE is_open = 0
              AND close_date >= ?
              AND close_date < ?
            ORDER BY close_date
            """,
            (week_start.strftime("%Y-%m-%d %H:%M:%S"),
             week_end.strftime("%Y-%m-%d %H:%M:%S")),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("Database error: %s", exc)
        return []
    finally:
        conn.close()


def fetch_alltime_stats(db_path: str) -> dict[str, Any]:
    """Fetch all-time statistics from the database."""
    if not os.path.exists(db_path):
        return {"total_trades": 0, "wins": 0, "win_rate": 0.0, "total_profit_pct": 0.0}

    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT close_profit_abs, close_profit AS profit_ratio, stake_amount
            FROM trades
            WHERE is_open = 0
            ORDER BY close_date
            """
        ).fetchall()

        if not rows:
            return {"total_trades": 0, "wins": 0, "win_rate": 0.0, "total_profit_pct": 0.0}

        total = len(rows)
        wins = sum(1 for r in rows if (r["profit_ratio"] or 0) > 0)
        total_profit = sum(r["close_profit_abs"] or 0 for r in rows)
        total_stake = sum(r["stake_amount"] or 0 for r in rows) or 1

        return {
            "total_trades": total,
            "wins": wins,
            "win_rate": wins / total * 100 if total else 0.0,
            "total_profit_pct": total_profit / total_stake * 100,
        }
    except sqlite3.Error as exc:
        logger.error("Database error (alltime): %s", exc)
        return {"total_trades": 0, "wins": 0, "win_rate": 0.0, "total_profit_pct": 0.0}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Statistics computation
# ---------------------------------------------------------------------------
def compute_weekly_stats(trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute weekly statistics from a list of closed trades."""
    if not trades:
        return {}

    total = len(trades)
    wins = [t for t in trades if (t["profit_ratio"] or 0) > 0]
    losses = [t for t in trades if (t["profit_ratio"] or 0) <= 0]
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = win_count / total * 100 if total else 0.0

    total_profit_abs = sum(t["close_profit_abs"] or 0 for t in trades)
    total_stake = sum(t["stake_amount"] or 0 for t in trades) or 1
    weekly_pnl_pct = total_profit_abs / total_stake * 100

    # Best and worst trades (by profit_ratio percentage)
    best = max(trades, key=lambda t: t["profit_ratio"] or 0)
    worst = min(trades, key=lambda t: t["profit_ratio"] or 0)

    # Average trade duration
    durations = []
    for t in trades:
        if t.get("open_date") and t.get("close_date"):
            # Fallback: compute from dates
            try:
                open_dt = _parse_date(t["open_date"])
                close_dt = _parse_date(t["close_date"])
                if open_dt and close_dt:
                    durations.append((close_dt - open_dt).total_seconds() / 60)
            except Exception:
                pass

    avg_duration_min = sum(durations) / len(durations) if durations else 0

    # Max drawdown within the week (cumulative P&L based)
    cum_pnl = 0.0
    peak_pnl = 0.0
    max_dd_pct = 0.0
    for t in trades:
        cum_pnl += t["close_profit_abs"] or 0
        peak_pnl = max(peak_pnl, cum_pnl)
        if peak_pnl > 0:
            dd = (cum_pnl - peak_pnl) / peak_pnl * 100
            max_dd_pct = min(max_dd_pct, dd)

    return {
        "total": total,
        "wins": win_count,
        "losses": loss_count,
        "win_rate": win_rate,
        "weekly_pnl_pct": weekly_pnl_pct,
        "total_profit_abs": total_profit_abs,
        "best_pair": best["pair"],
        "best_pnl_pct": (best["profit_ratio"] or 0) * 100,
        "worst_pair": worst["pair"],
        "worst_pnl_pct": (worst["profit_ratio"] or 0) * 100,
        "avg_duration_min": avg_duration_min,
        "max_drawdown_pct": max_dd_pct,
    }


def _parse_date(dt_str: str) -> datetime | None:
    """Parse a date string from Freqtrade DB (multiple formats)."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(dt_str.split("+")[0].strip(), fmt)
        except ValueError:
            continue
    return None


def _format_duration(minutes: float) -> str:
    """Format minutes into human-readable duration (e.g., '3h 45m')."""
    if minutes < 1:
        return "<1m"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------
def build_weekly_chart(trades: list[dict[str, Any]], week_start: datetime, week_end: datetime) -> bytes:
    """Generate a weekly equity curve chart and return as PNG bytes."""
    # Build cumulative P&L series
    dates: list[datetime] = []
    cum_pnl: list[float] = []
    running = 0.0

    for t in trades:
        dt = _parse_date(t["close_date"])
        if dt is None:
            continue
        running += (t["profit_ratio"] or 0) * 100  # accumulate as percentage
        dates.append(dt)
        cum_pnl.append(running)

    if not dates:
        return b""

    # Insert starting point at week_start with 0%
    dates.insert(0, week_start)
    cum_pnl.insert(0, 0.0)

    final_pnl = cum_pnl[-1]
    line_color = EQUITY_COLOR if final_pnl >= 0 else NEGATIVE_COLOR

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.6)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)

    # Plot equity line
    ax.plot(dates, cum_pnl, color=line_color, linewidth=2.2, zorder=3)
    ax.fill_between(dates, 0, cum_pnl, alpha=EQUITY_FILL_ALPHA, color=line_color, zorder=2)

    # Zero line
    ax.axhline(y=0, color=TEXT_COLOR, linewidth=0.6, alpha=0.3, linestyle="--")

    # Title
    week_start_str = week_start.strftime("%b %d")
    week_end_display = (week_end - timedelta(days=1)).strftime("%b %d, %Y")
    ax.set_title(
        f"TrendRider Weekly Report | {week_start_str} \u2013 {week_end_display}",
        fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=15,
    )
    ax.set_ylabel("Cumulative P&L (%)", fontsize=11, color=TEXT_COLOR)
    ax.set_xlabel("", fontsize=1)

    # Format axes
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%+.1f%%"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=8)

    # Annotate final value
    ax.annotate(
        f"{final_pnl:+.2f}%",
        xy=(dates[-1], cum_pnl[-1]),
        xytext=(10, 12), textcoords="offset points",
        fontsize=11, fontweight="bold", color=line_color,
        arrowprops=dict(arrowstyle="->", color=line_color, lw=1.2),
    )

    # Watermark
    fig.text(
        0.95, 0.02, WATERMARK,
        fontsize=8, color=TEXT_COLOR, alpha=0.3,
        ha="right", va="bottom", style="italic",
    )

    # TrendRider branding top-right
    fig.text(
        0.95, 0.96, "trendrider.net",
        fontsize=8, color=ACCENT_COLOR, alpha=0.5,
        ha="right", va="top",
    )

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------
def format_weekly_message(
    stats: dict[str, Any],
    alltime: dict[str, Any],
    week_start: datetime,
    week_end: datetime,
) -> str:
    """Format the weekly report Telegram message."""
    start_str = week_start.strftime("%b %d")
    end_str = (week_end - timedelta(days=1)).strftime("%b %d, %Y")

    pnl_sign = "+" if stats["weekly_pnl_pct"] >= 0 else ""
    best_sign = "+" if stats["best_pnl_pct"] >= 0 else ""
    worst_sign = "+" if stats["worst_pnl_pct"] >= 0 else ""
    alltime_sign = "+" if alltime["total_profit_pct"] >= 0 else ""

    duration_str = _format_duration(stats["avg_duration_min"])

    best_pair_short = stats["best_pair"].replace("/USDT:USDT", "").replace("/USDT", "")
    worst_pair_short = stats["worst_pair"].replace("/USDT:USDT", "").replace("/USDT", "")

    lines = [
        f"\U0001f4ca Weekly Report | {start_str}\u2013{end_str}",
        "\u2501" * 21,
        "",
        f"\U0001f4c8 Trades: {stats['total']} closed",
        f"\U0001f3c6 Win Rate: {stats['win_rate']:.1f}% ({stats['wins']}W / {stats['losses']}L)",
        f"\U0001f4b0 Weekly P&L: {pnl_sign}{stats['weekly_pnl_pct']:.2f}%",
        "",
        f"\U0001f51d Best: {best_pair_short} {best_sign}{stats['best_pnl_pct']:.2f}%",
        f"\U0001f4c9 Worst: {worst_pair_short} {worst_sign}{stats['worst_pnl_pct']:.2f}%",
        f"\u23f1 Avg Duration: {duration_str}",
    ]

    if stats["max_drawdown_pct"] < 0:
        lines.append(f"\U0001f6a8 Max Drawdown: {stats['max_drawdown_pct']:.2f}%")

    lines += [
        "",
        "\U0001f4ca All-Time Stats:",
        f"\U0001f3c6 {alltime['win_rate']:.1f}% Win Rate | {alltime['total_trades']} Trades",
        f"\U0001f4b0 Total: {alltime_sign}{alltime['total_profit_pct']:.1f}%",
        "",
        "\u2501" * 21,
        "\U0001f680 Get real-time signals!",
        "\U0001f449 @TrendRiderSignals",
        "\U0001f310 trendrider.net",
    ]
    return "\n".join(lines)


def format_no_trades_message(week_start: datetime, week_end: datetime) -> str:
    """Format message when there were no trades this week."""
    start_str = week_start.strftime("%b %d")
    end_str = (week_end - timedelta(days=1)).strftime("%b %d, %Y")
    return (
        f"\U0001f4ca Weekly Report | {start_str}\u2013{end_str}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        f"\U0001f4a4 No trades this week, market was quiet.\n"
        f"The bot is monitoring and waiting for optimal setups.\n\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f449 @TrendRiderSignals\n"
        f"\U0001f310 trendrider.net"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="TrendRider Weekly Report Generator")
    parser.add_argument("--dry-run", action="store_true", help="Save PNG locally, don't send to Telegram")
    parser.add_argument("--save", type=str, default=None, help="Save PNG to specified path")
    parser.add_argument("--weeks-ago", type=int, default=0, help="Generate report for N weeks ago (0 = current)")
    args = parser.parse_args()

    logger.info("Weekly report started")

    # Determine week boundaries (Monday 00:00 UTC to next Monday 00:00 UTC)
    now = datetime.now(timezone.utc)
    # Go back to most recent Monday
    days_since_monday = now.weekday()  # Monday=0
    this_monday = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
    week_end = this_monday - timedelta(weeks=args.weeks_ago)
    week_start = week_end - timedelta(weeks=1)

    logger.info("Report period: %s to %s", week_start.isoformat(), week_end.isoformat())

    # Fetch data
    trades = fetch_weekly_trades(DB_PATH, week_start, week_end)
    logger.info("Found %d closed trades in period", len(trades))

    token, channel_id = get_telegram_config()

    # No trades case
    if not trades:
        msg = format_no_trades_message(week_start, week_end)
        logger.info("No trades this week")
        if args.dry_run:
            print(msg)
        else:
            if token and channel_id:
                send_text(token, channel_id, msg)
                logger.info("No-trades message sent to channel")
            else:
                logger.error("Missing Telegram credentials (TG_TOKEN / FREE_CHANNEL_ID)")
        return

    # Compute stats
    stats = compute_weekly_stats(trades)
    alltime = fetch_alltime_stats(DB_PATH)
    caption = format_weekly_message(stats, alltime, week_start, week_end)

    # Build chart
    png_bytes = build_weekly_chart(trades, week_start, week_end)

    # Save if requested
    if args.save:
        with open(args.save, "wb") as f:
            f.write(png_bytes)
        logger.info("Chart saved to %s", args.save)

    if args.dry_run:
        print(caption)
        print()
        if not args.save and png_bytes:
            out_path = os.path.join(os.getcwd(), "weekly_report.png")
            with open(out_path, "wb") as f:
                f.write(png_bytes)
            print(f"Dry run — chart saved to {out_path}")
        return

    # Send to Telegram
    if not token or not channel_id:
        logger.error("Missing Telegram credentials (TG_TOKEN / FREE_CHANNEL_ID)")
        sys.exit(1)

    if png_bytes:
        logger.info("Sending weekly report with chart to channel %s", channel_id)
        send_photo(token, channel_id, png_bytes, caption)
    else:
        logger.warning("Chart generation returned empty, sending text only")
        send_text(token, channel_id, caption)

    logger.info("Weekly report sent successfully")


if __name__ == "__main__":
    main()
