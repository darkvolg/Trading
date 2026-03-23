#!/usr/bin/env python3
"""
TrendRider Signals — Telegram Channel Bot.
Standalone bot running alongside Freqtrade with interactive commands.
"""

import json
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from shared_utils import calc_command, query_stats

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.getenv("FT_DB_PATH", os.path.join(FT_HOME, "tradesv3.dryrun.sqlite"))
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))


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


# ── /stats ───────────────────────────────────────────────────────────────

async def stats_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trading statistics for the last 30 days."""
    try:
        text = query_stats(DB_PATH)
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
