#!/usr/bin/env python3
"""
TrendRider Signals — Telegram Channel Bot.
Standalone bot running alongside Freqtrade with interactive commands.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("FT_DB_PATH", "/opt/freqtrade/tradesv3.dryrun.sqlite")
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", "/opt/freqtrade/config.json")


def get_credentials() -> tuple[str, str]:
    """Return (TG_TOKEN, TG_CHAT_ID) from env vars or Freqtrade config."""
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if token and chat_id:
        return token, chat_id

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        tg = cfg.get("telegram", {})
        token = token or tg.get("token", "")
        chat_id = chat_id or str(tg.get("chat_id", ""))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Cannot read config: %s", exc)

    if not token:
        raise RuntimeError("TG_TOKEN is not set and not found in config.json")
    return token, chat_id


# ── /calc ────────────────────────────────────────────────────────────────

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


# ── /stats ───────────────────────────────────────────────────────────────

def _query_stats() -> str:
    """Read Freqtrade SQLite and build stats message."""
    if not os.path.exists(DB_PATH):
        return "*TRENDRIDER STATS*\n\nNo database found. Bot may not have started yet."

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cur.execute(
        """
        SELECT id, pair, open_date, close_date, open_rate, close_rate,
               profit_abs, profit_ratio, stake_amount, is_open
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
            "============================\n_TrendRider Algo | @TrendRiderSignals_"
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
        short = pair.replace("/USDT", "").replace("/USDT:USDT", "")
        sign = "+" if data["profit"] >= 0 else ""
        lines.append(f"  {short}: {data['count']} trades, {sign}${data['profit']:.2f}")

    lines += [
        "",
        "============================",
        "_TrendRider Algo | @TrendRiderSignals_",
    ]
    return "\n".join(lines)


async def stats_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trading statistics for the last 30 days."""
    try:
        text = _query_stats()
    except Exception as exc:
        logger.exception("Stats query failed")
        text = f"Error reading stats: {exc}"
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /help ────────────────────────────────────────────────────────────────

HELP_TEXT = (
    "*TrendRider Signals Bot*\n"
    "============================\n"
    "Available commands:\n\n"
    "`/calc <deposit> <risk%>` — Risk calculator\n"
    "  _Example: /calc 1000 2_\n\n"
    "`/stats` — Trading stats (last 30 days)\n\n"
    "`/help` — This message\n"
    "============================\n"
    "_@TrendRiderSignals_"
)


async def help_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message."""
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


# ── main ─────────────────────────────────────────────────────────────────

def main() -> None:
    token, _ = get_credentials()
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("calc", calc_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", help_command))

    logger.info("TrendRider channel bot started (polling)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
