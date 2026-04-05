"""
Shared utilities for TrendRider Telegram bots.
Extracted from channel_bot.py and subscription_bot.py to avoid duplication.
"""

import os
import sqlite3
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import ContextTypes


def query_stats(db_path: str) -> str:
    """Read Freqtrade SQLite and build stats message.

    Args:
        db_path: Path to the Freqtrade trades SQLite database.
    """
    if not os.path.exists(db_path):
        return "*TRENDRIDER STATS*\n\nNo database found. Bot may not have started yet."

    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cur.execute(
        """
        SELECT id, pair, open_date, close_date, open_rate, close_rate,
               close_profit_abs AS profit_abs, close_profit AS profit_ratio,
               stake_amount, is_open
        FROM trades
        WHERE open_date >= ?
        ORDER BY open_date DESC
        """,
        (since,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return (
            "*TRENDRIDER STATS*\n============================\n"
            "No trades yet. Bot is monitoring markets.\n"
            "============================\n_TrendRider AI | @TrendRiderSignals_"
        )

    total = len(rows)
    open_trades = sum(1 for r in rows if r["is_open"])
    closed = [r for r in rows if not r["is_open"]]
    wins = [r for r in closed if (r["profit_abs"] or 0) > 0]
    losses = [r for r in closed if (r["profit_abs"] or 0) <= 0]
    win_rate = len(wins) / len(closed) * 100 if closed else 0

    total_profit = sum(r["profit_abs"] or 0 for r in closed)
    avg_profit = total_profit / len(closed) if closed else 0

    total_stake = sum(r["stake_amount"] or 0 for r in closed) or 1
    total_profit_pct = total_profit / total_stake * 100
    avg_profit_pct = avg_profit / (total_stake / len(closed)) * 100 if closed else 0

    best = max(closed, key=lambda r: r["profit_abs"] or 0) if closed else None
    worst = min(closed, key=lambda r: r["profit_abs"] or 0) if closed else None

    # By pair
    pair_map: dict[str, dict] = {}
    for r in closed:
        pair = r["pair"]
        entry = pair_map.setdefault(pair, {"count": 0, "profit": 0.0})
        entry["count"] += 1
        entry["profit"] += r["profit_abs"] or 0

    lines = [
        "*TRENDRIDER STATS*",
        "============================",
        "Period: last 30 days",
        "",
        f"Trades: {total} | Open: {open_trades}",
        f"Win: {len(wins)} | Loss: {len(losses)}",
        f"Win Rate: {win_rate:.1f}%",
        "",
        f"Total Profit: {'+' if total_profit >= 0 else ''}${total_profit:.2f}"
        f" ({'+' if total_profit_pct >= 0 else ''}{total_profit_pct:.2f}%)",
        f"Avg Profit: {'+' if avg_profit >= 0 else ''}${avg_profit:.2f}"
        f" ({'+' if avg_profit_pct >= 0 else ''}{avg_profit_pct:.2f}%)",
    ]

    if best:
        bp = (best["profit_ratio"] or 0) * 100
        lines.append(
            f"Best: {best['pair']} {'+' if best['profit_abs'] >= 0 else ''}"
            f"${best['profit_abs']:.2f} ({'+' if bp >= 0 else ''}{bp:.1f}%)"
        )
    if worst:
        wp = (worst["profit_ratio"] or 0) * 100
        lines.append(
            f"Worst: {worst['pair']} {'+' if worst['profit_abs'] >= 0 else ''}"
            f"${worst['profit_abs']:.2f} ({'+' if wp >= 0 else ''}{wp:.1f}%)"
        )

    lines.append("")
    lines.append("By Pair:")
    for pair, data in sorted(pair_map.items(), key=lambda x: -x[1]["profit"]):
        short = pair.replace("/USDT:USDT", "").replace("/USDT", "")
        sign = "+" if data["profit"] >= 0 else ""
        lines.append(f"  {short}: {data['count']} trades, {sign}${data['profit']:.2f}")

    lines += [
        "",
        "============================",
        "_TrendRider AI | @TrendRiderSignals_",
    ]
    return "\n".join(lines)


async def calc_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Risk calculator: /calc <deposit> <risk_percent>"""
    args = ctx.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/calc <deposit> <risk_percent>`\nExample: `/calc 1000 2`",
            parse_mode="Markdown",
        )
        return

    try:
        deposit = float(args[0])
        risk_pct = float(args[1])
    except ValueError:
        await update.message.reply_text("Please provide valid numbers.")
        return

    risk_amount = deposit * risk_pct / 100

    lines = [
        "*RISK CALCULATOR*",
        "============================",
        f"Deposit: ${deposit:,.0f}",
        f"Risk per trade: {risk_pct}% (${risk_amount:,.2f})",
        "",
    ]

    for sl_pct in (6, 3):
        pos_size = risk_amount / (sl_pct / 100)
        margin = pos_size / 3
        lines += [
            f"With SL at -{sl_pct}% {'(TrendRider default)' if sl_pct == 6 else ''}:",
            f"  Position size: ${pos_size:,.2f}",
            f"  With 3x leverage: margin ${margin:,.2f}",
            f"  Max loss: ${risk_amount:,.2f}",
            "",
        ]

    lines += [
        "============================",
        "_Adjust risk to your comfort level_",
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
