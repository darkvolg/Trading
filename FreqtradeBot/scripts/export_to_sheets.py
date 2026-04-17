#!/usr/bin/env python3
"""Export Freqtrade trades from SQLite to Google Sheets (incremental).

Appends only NEW closed trades since last export. Tracks progress via
.last_sheets_export_id file so re-runs are safe and idempotent.

After exporting trades, updates the Dashboard worksheet with calculated
metrics (win rate, P&L, drawdown, profit factor, SQN, monthly breakdown).

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
import math
import os
import sqlite3
from collections import defaultdict
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


def calc_duration_hours(open_date: str, close_date: str) -> float:
    """Calculate trade duration in hours (numeric)."""
    if not open_date or not close_date:
        return 0.0
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        od = datetime.strptime(open_date[:19], fmt)
        cd = datetime.strptime(close_date[:19], fmt)
        return (cd - od).total_seconds() / 3600
    except (ValueError, TypeError):
        return 0.0


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


def append_rows(spreadsheet_id: str, rows: list[list[str]], gc: gspread.Client | None = None) -> tuple[gspread.Spreadsheet, int]:
    """Append rows to the Trades sheet. Returns (spreadsheet, count)."""
    if gc is None:
        gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)

    # Find the Trades worksheet (handle both old single-sheet and new two-sheet layouts)
    try:
        ws = sh.worksheet("Trades")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.sheet1

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    return sh, len(rows)


# ---------------------------------------------------------------------------
# Dashboard metrics calculation
# ---------------------------------------------------------------------------

def calculate_metrics(trades: list[dict]) -> dict:
    """Calculate all dashboard metrics from trade data."""
    if not trades:
        return {}

    total = len(trades)
    profits = [t["profit_abs"] or 0 for t in trades]
    ratios = [t["profit_ratio"] or 0 for t in trades]

    wins = sum(1 for r in ratios if r > 0)
    total - wins
    win_rate = (wins / total) * 100 if total else 0

    total_pnl_usdt = sum(profits)
    total_pnl_pct = sum(ratios) * 100

    # Max drawdown (peak-to-trough on cumulative P&L)
    cumulative = []
    running = 0.0
    for p in profits:
        running += p
        cumulative.append(running)

    peak = cumulative[0]
    max_dd = 0.0
    for val in cumulative:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd
    # Express as percentage of peak (avoid div/0)
    max_dd_pct = (max_dd / peak * 100) if peak > 0 else 0.0

    # Profit factor = gross profit / gross loss
    gross_profit = sum(p for p in profits if p > 0)
    gross_loss = abs(sum(p for p in profits if p < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    # SQN = sqrt(N) * mean(R) / stdev(R), where R = trade returns
    if len(ratios) >= 2:
        mean_r = sum(ratios) / len(ratios)
        variance = sum((r - mean_r) ** 2 for r in ratios) / (len(ratios) - 1)
        stdev_r = math.sqrt(variance) if variance > 0 else 0
        sqn = (math.sqrt(len(ratios)) * mean_r / stdev_r) if stdev_r > 0 else 0
    else:
        sqn = 0

    # Best / worst trade
    best_idx = max(range(total), key=lambda i: profits[i])
    worst_idx = min(range(total), key=lambda i: profits[i])
    best_t = trades[best_idx]
    worst_t = trades[worst_idx]

    best_str = f"{best_t['pair']}  ${profits[best_idx]:+.2f} ({ratios[best_idx]*100:+.1f}%)"
    worst_str = f"{worst_t['pair']}  ${profits[worst_idx]:+.2f} ({ratios[worst_idx]*100:+.1f}%)"

    # Average duration
    durations = [calc_duration_hours(t["open_date"], t["close_date"]) for t in trades]
    avg_dur_h = sum(durations) / len(durations) if durations else 0
    if avg_dur_h < 1:
        avg_dur_str = f"{int(avg_dur_h * 60)}m"
    else:
        avg_dur_str = f"{avg_dur_h:.1f}h"

    return {
        "total_trades": total,
        "win_rate": round(win_rate, 1),
        "total_pnl_usdt": round(total_pnl_usdt, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "N/A (no losses)",
        "sqn": round(sqn, 2),
        "best_trade": best_str,
        "worst_trade": worst_str,
        "avg_duration": avg_dur_str,
    }


def calculate_monthly(trades: list[dict]) -> list[list[str]]:
    """Calculate monthly breakdown rows."""
    monthly: dict[str, list[dict]] = defaultdict(list)

    for t in trades:
        close = t.get("close_date") or ""
        if not close:
            continue
        month_key = close[:7]  # "YYYY-MM"
        monthly[month_key].append(t)

    rows = []
    for month in sorted(monthly.keys()):
        mt = monthly[month]
        count = len(mt)
        wins = sum(1 for t in mt if (t["profit_ratio"] or 0) > 0)
        losses = count - wins
        win_pct = round((wins / count) * 100, 1) if count else 0
        pnl_usdt = round(sum(t["profit_abs"] or 0 for t in mt), 2)
        pnl_pct = round(sum((t["profit_ratio"] or 0) * 100 for t in mt), 2)
        # Leading space forces Sheets to treat "+N" values as text (not formula)
        rows.append([month, str(count), str(wins), str(losses), f"{win_pct}", f" {pnl_usdt:+.2f}", f" {pnl_pct:+.2f}"])

    return rows


# ---------------------------------------------------------------------------
# Dashboard update
# ---------------------------------------------------------------------------

DASHBOARD_METRIC_LABELS = [
    "Total Trades",
    "Win Rate (%)",
    "Total P&L (USDT)",
    "Total P&L (%)",
    "Max Drawdown (%)",
    "Profit Factor",
    "SQN Score",
    "Best Trade",
    "Worst Trade",
    "Average Trade Duration",
]

MONTHLY_HEADERS = ["Month", "Trades", "Wins", "Losses", "Win%", "P&L USDT", "P&L %"]


def ensure_dashboard(sh: gspread.Spreadsheet) -> gspread.Worksheet:
    """Get or create the Dashboard worksheet."""
    try:
        return sh.worksheet("Dashboard")
    except gspread.exceptions.WorksheetNotFound:
        # Create a minimal dashboard (the full formatted one comes from setup_sheets.py)
        dash = sh.add_worksheet(title="Dashboard", rows=100, cols=10)

        # Basic header
        dash.merge_cells("A1:G1")
        dash.update("A1", [["TrendRider  --  Live P&L Tracker"]], value_input_option="USER_ENTERED")
        dash.format("A1:G1", {
            "textFormat": {"bold": True, "fontSize": 16},
            "horizontalAlignment": "CENTER",
        })

        dash.merge_cells("A2:G2")
        dash.update("A2", [["Updated every 6 hours  |  View only"]], value_input_option="USER_ENTERED")
        dash.format("A2:G2", {
            "textFormat": {"italic": True, "fontSize": 10,
                           "foregroundColor": {"red": 0.6, "green": 0.6, "blue": 0.6}},
            "horizontalAlignment": "CENTER",
        })

        # Section headers
        dash.merge_cells("A4:B4")
        dash.update("A4", [["KEY METRICS"]], value_input_option="USER_ENTERED")
        dash.format("A4:B4", {
            "textFormat": {"bold": True, "fontSize": 12},
            "backgroundColor": {"red": 0.18, "green": 0.46, "blue": 0.82},
        })

        # Metric labels
        label_cells = [[label] for label in DASHBOARD_METRIC_LABELS]
        dash.update(f"A5:A{5 + len(DASHBOARD_METRIC_LABELS) - 1}", label_cells, value_input_option="USER_ENTERED")
        dash.format(f"A5:A{5 + len(DASHBOARD_METRIC_LABELS) - 1}", {"textFormat": {"bold": True}})

        monthly_start = 5 + len(DASHBOARD_METRIC_LABELS) + 2
        dash.merge_cells(f"A{monthly_start}:G{monthly_start}")
        dash.update(f"A{monthly_start}", [["MONTHLY BREAKDOWN"]], value_input_option="USER_ENTERED")
        dash.format(f"A{monthly_start}:G{monthly_start}", {
            "textFormat": {"bold": True, "fontSize": 12},
            "backgroundColor": {"red": 0.18, "green": 0.46, "blue": 0.82},
        })

        header_row = monthly_start + 1
        dash.update(f"A{header_row}:G{header_row}", [MONTHLY_HEADERS], value_input_option="USER_ENTERED")
        dash.format(f"A{header_row}:G{header_row}", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
            "horizontalAlignment": "CENTER",
        })

        # Move to first position
        sh.batch_update({"requests": [{
            "updateSheetProperties": {
                "properties": {"sheetId": dash.id, "index": 0},
                "fields": "index",
            }
        }]})

        return dash


def update_dashboard(sh: gspread.Spreadsheet, trades: list[dict]) -> None:
    """Update the Dashboard worksheet with calculated metrics from trades.

    Reads ALL trades from the Trades sheet (not just newly exported ones)
    to compute lifetime metrics.
    """
    # Load all trades from Trades sheet for complete metrics
    all_trades = _load_all_trades_from_sheet(sh)

    # If the sheet is empty but we have DB trades, use those
    if not all_trades and trades:
        all_trades = trades

    if not all_trades:
        print("Dashboard: no trades to summarize.")
        return

    dash = ensure_dashboard(sh)
    metrics = calculate_metrics(all_trades)

    # Write metric values (column B, rows 5-14)
    metric_values = [
        [str(metrics["total_trades"])],
        [f'{metrics["win_rate"]}%'],
        [f'${metrics["total_pnl_usdt"]:+.2f}'],
        [f' {metrics["total_pnl_pct"]:+.2f}%'],  # leading space: avoid Sheets formula parsing
        [f'{metrics["max_drawdown_pct"]:.2f}%'],
        [str(metrics["profit_factor"])],
        [str(metrics["sqn"])],
        [metrics["best_trade"]],
        [metrics["worst_trade"]],
        [metrics["avg_duration"]],
    ]
    dash.update(values=metric_values, range_name=f"B5:B{5 + len(metric_values) - 1}", value_input_option="USER_ENTERED")

    # Color P&L cells: green if positive, red if negative
    pnl_usdt = metrics["total_pnl_usdt"]
    pnl_color = (
        {"red": 0.0, "green": 0.55, "blue": 0.2} if pnl_usdt >= 0
        else {"red": 0.8, "green": 0.1, "blue": 0.1}
    )
    dash.format("B7", {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": pnl_color}})
    dash.format("B8", {"textFormat": {"bold": True, "foregroundColor": pnl_color}})

    # Monthly breakdown
    monthly_rows = calculate_monthly(all_trades)
    monthly_data_start = 5 + len(DASHBOARD_METRIC_LABELS) + 2 + 2  # row 19

    if monthly_rows:
        # Clear old monthly data (up to 60 rows should be plenty)
        clear_range = f"A{monthly_data_start}:G{monthly_data_start + 60}"
        dash.batch_clear([clear_range])

        # Write new monthly data
        end_row = monthly_data_start + len(monthly_rows) - 1
        dash.update(
            values=monthly_rows,
            range_name=f"A{monthly_data_start}:G{end_row}",
            value_input_option="USER_ENTERED",
        )

        # Color monthly P&L cells
        for i, row in enumerate(monthly_rows):
            row_num = monthly_data_start + i
            pnl_val = float(row[5])  # P&L USDT column
            color = (
                {"red": 0.0, "green": 0.55, "blue": 0.2} if pnl_val >= 0
                else {"red": 0.8, "green": 0.1, "blue": 0.1}
            )
            dash.format(f"F{row_num}:G{row_num}", {"textFormat": {"foregroundColor": color}})

    # Update timestamp in row 2
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    dash.update(values=[[f"Last updated: {now_str}  |  View only"]], range_name="A2", value_input_option="USER_ENTERED")

    print(f"Dashboard updated: {metrics['total_trades']} trades, P&L ${metrics['total_pnl_usdt']:+.2f}")


def _load_all_trades_from_sheet(sh: gspread.Spreadsheet) -> list[dict]:
    """Load all trade rows from the Trades worksheet and convert back to dicts.

    Used to compute lifetime metrics even during incremental exports.
    Falls back to empty list if the sheet is missing or empty.
    """
    try:
        ws = sh.worksheet("Trades")
    except gspread.exceptions.WorksheetNotFound:
        return []

    all_values = ws.get_all_values()
    if len(all_values) <= 1:  # header only or empty
        return []

    # Parse sheet rows back into trade-like dicts
    # Columns: Date, Pair, Direction, Entry, Exit, Stake, P&L USDT, P&L %, Duration, Strategy, Exit Reason
    trades = []
    for row in all_values[1:]:
        if len(row) < 11 or not row[0]:
            continue
        try:
            pnl_usdt = float(row[6]) if row[6] else 0
            pnl_pct = float(row[7]) if row[7] else 0
            trades.append({
                "close_date": row[0].replace("T", " "),
                "open_date": "",  # not stored in sheet; duration already calculated
                "pair": row[1],
                "profit_abs": pnl_usdt,
                "profit_ratio": pnl_pct / 100,  # convert back to ratio
                "stake_amount": float(row[5]) if row[5] else 0,
            })
        except (ValueError, IndexError):
            continue

    return trades


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

    # Build rows and append (reuse the gc/sh for dashboard update)
    gc = get_gspread_client()
    rows = [trade_to_row(t) for t in trades]
    sh, count = append_rows(SHEETS_ID, rows, gc=gc)
    print(f"Appended {count} rows to Google Sheet.")

    # Update tracker with the highest trade ID
    max_id = max(t["id"] for t in trades)
    write_last_id(TRACKER_FILE, max_id)
    print(f"Tracker updated: last_id = {max_id}")

    # Update Dashboard with lifetime metrics
    try:
        update_dashboard(sh, trades)
    except Exception as e:
        print(f"WARNING: Dashboard update failed: {e}")
        print("Trade export succeeded. Dashboard can be retried.")

    # Telegram
    if args.notify:
        send_telegram(count, trades)


if __name__ == "__main__":
    main()
