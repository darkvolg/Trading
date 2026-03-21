#!/usr/bin/env python3
"""Export Freqtrade trades from SQLite to Google Sheets (incremental).

Appends only NEW closed trades since last export. Tracks progress via
.last_sheets_export_id file so re-runs are safe and idempotent.

Usage:
    python export_to_sheets.py              # export only
    python export_to_sheets.py --notify     # export + send Telegram summary
    python export_to_sheets.py --full       # re-export all trades (ignore tracker)

Env vars:
    GOOGLE_SHEETS_ID        — target spreadsheet ID (required)
    GOOGLE_CREDENTIALS_FILE — path to service account JSON
                              (default: FT_HOME/secrets/service-account.json)
    FT_HOME                 — freqtrade base directory
    TG_TOKEN / TG_CHAT_ID   — Telegram bot credentials (or read from config.json)
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# Paths (same pattern as export_trades.py)
# ---------------------------------------------------------------------------

FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.getenv("FT_DB_PATH", os.path.join(FT_HOME, "tradesv3.dryrun.sqlite"))
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))
CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE",
    os.path.join(FT_HOME, "secrets", "service-account.json"),
)
SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
TRACKER_FILE = os.path.join(FT_HOME, ".last_sheets_export_id")

# ---------------------------------------------------------------------------
# Sheet columns
# ---------------------------------------------------------------------------

SHEET_COLUMNS = [
    "Date", "Pair", "Direction", "Entry", "Exit",
    "Stake", "P&L USDT", "P&L %", "Duration", "Strategy", "Exit Reason",
]

# ---------------------------------------------------------------------------
# DB query — fetches trades with id > last_exported_id
# ---------------------------------------------------------------------------

QUERY_NEW = """
SELECT id, pair, open_date, close_date, open_rate, close_rate,
       close_profit AS profit_ratio, close_profit_abs AS profit_abs,
       exit_reason, leverage, stake_amount, strategy
FROM trades
WHERE is_open = 0 AND id > ?
ORDER BY id ASC
"""

QUERY_ALL = """
SELECT id, pair, open_date, close_date, open_rate, close_rate,
       close_profit AS profit_ratio, close_profit_abs AS profit_abs,
       exit_reason, leverage, stake_amount, strategy
FROM trades
WHERE is_open = 0
ORDER BY id ASC
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_new_trades(db_path: str, last_id: int) -> list[dict]:
    """Load closed trades with id > last_id."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(QUERY_NEW, (last_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def load_all_trades(db_path: str) -> list[dict]:
    """Load all closed trades."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(QUERY_ALL).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fmt_dt(val: str | None) -> str:
    if not val:
        return ""
    return val.replace(" ", "T")[:19]


def calc_duration(open_date: str, close_date: str) -> str:
    """Calculate trade duration from open/close dates."""
    if not open_date or not close_date:
        return "0h"
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        od = datetime.strptime(open_date[:19], fmt)
        cd = datetime.strptime(close_date[:19], fmt)
        hours = (cd - od).total_seconds() / 3600
        if hours < 1:
            return f"{int(hours * 60)}m"
        return f"{hours:.1f}h"
    except (ValueError, TypeError):
        return "N/A"


def trade_to_row(t: dict) -> list[str]:
    """Convert a trade dict to a list of cell values for the sheet."""
    side = "short" if (t.get("leverage") or 1) < 0 else "long"
    return [
        fmt_dt(t["close_date"]),
        t["pair"],
        side,
        f'{t["open_rate"]:.6f}',
        f'{t["close_rate"]:.6f}',
        f'{t["stake_amount"] or 0:.2f}',
        f'{t["profit_abs"] or 0:.4f}',
        f'{(t["profit_ratio"] or 0) * 100:.2f}',
        calc_duration(t["open_date"], t["close_date"]),
        t.get("strategy") or "",
        t["exit_reason"] or "",
    ]


# ---------------------------------------------------------------------------
# Tracker (last exported trade ID)
# ---------------------------------------------------------------------------

def read_last_id(path: str) -> int:
    try:
        return int(Path(path).read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_last_id(path: str, trade_id: int) -> None:
    Path(path).write_text(str(trade_id))


# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_gspread_client() -> gspread.Client:
    """Authenticate via service account and return gspread client."""
    if not Path(CREDENTIALS_FILE).exists():
        raise FileNotFoundError(
            f"Service account credentials not found: {CREDENTIALS_FILE}\n"
            "Set GOOGLE_CREDENTIALS_FILE or place the JSON at the default path."
        )
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def append_rows(spreadsheet_id: str, rows: list[list[str]]) -> int:
    """Append rows to the first sheet. Returns number of rows appended."""
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.sheet1
    ws.append_rows(rows, value_input_option="USER_ENTERED")
    return len(rows)


# ---------------------------------------------------------------------------
# Telegram (same pattern as export_trades.py)
# ---------------------------------------------------------------------------

def send_telegram(new_count: int, trades: list[dict]) -> None:
    import requests

    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")

    if not token or not chat_id:
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            tg = cfg.get("telegram", {})
            token = token or tg.get("token", "")
            chat_id = chat_id or str(tg.get("chat_id", ""))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    if not token or not chat_id:
        print("Telegram credentials not found, skipping notification.")
        return

    total_pnl = sum(t["profit_abs"] or 0 for t in trades)
    wins = sum(1 for t in trades if (t["profit_ratio"] or 0) > 0)
    win_rate = round(wins / len(trades) * 100, 1) if trades else 0

    text = (
        f"📋 *Sheets Export*\n"
        f"Exported: {new_count} new trade(s)\n"
        f"P&L: ${total_pnl:+.2f} | Win rate: {win_rate}%\n"
    )

    # Top 3 by P&L
    sorted_trades = sorted(trades, key=lambda t: t["profit_abs"] or 0, reverse=True)
    if sorted_trades:
        text += "\nTop trades:\n"
        for t in sorted_trades[:3]:
            pnl = t["profit_abs"] or 0
            pct = (t["profit_ratio"] or 0) * 100
            text += f"  {t['pair']}: ${pnl:+.2f} ({pct:+.1f}%)\n"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    print("Telegram notification sent.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Export Freqtrade trades to Google Sheets")
    parser.add_argument("--notify", action="store_true", help="Send summary to Telegram")
    parser.add_argument("--full", action="store_true", help="Re-export all trades (ignore tracker)")
    args = parser.parse_args()

    # Validate config
    if not SHEETS_ID:
        print("ERROR: GOOGLE_SHEETS_ID env var is not set.")
        print("Run setup_sheets.py first to create a spreadsheet, then set the env var.")
        return

    if not Path(DB_PATH).exists():
        print(f"Database not found: {DB_PATH}")
        return

    # Load trades
    if args.full:
        trades = load_all_trades(DB_PATH)
        print(f"Full export: {len(trades)} closed trades.")
    else:
        last_id = read_last_id(TRACKER_FILE)
        trades = load_new_trades(DB_PATH, last_id)
        print(f"Incremental export: {len(trades)} new trades (last ID: {last_id}).")

    if not trades:
        print("No new trades to export.")
        return

    # Build rows and append
    rows = [trade_to_row(t) for t in trades]
    count = append_rows(SHEETS_ID, rows)
    print(f"Appended {count} rows to Google Sheet.")

    # Update tracker with the highest trade ID
    max_id = max(t["id"] for t in trades)
    write_last_id(TRACKER_FILE, max_id)
    print(f"Tracker updated: last_id = {max_id}")

    # Telegram
    if args.notify:
        send_telegram(count, trades)


if __name__ == "__main__":
    main()
