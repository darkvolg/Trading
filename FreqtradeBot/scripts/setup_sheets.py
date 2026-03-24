#!/usr/bin/env python3
"""One-time setup: create a Google Sheet for Freqtrade trade exports.

Creates a new spreadsheet with two worksheets:
  1. Dashboard — professional P&L summary with key metrics and monthly breakdown
  2. Trades   — raw trade data (headers only)

Makes the sheet public (read-only) and prints the spreadsheet ID + URL.

Usage:
    python setup_sheets.py
    python setup_sheets.py --name "My Trading Journal"

Env vars:
    GOOGLE_CREDENTIALS_FILE — path to service account JSON
                              (default: FT_HOME/secrets/service-account.json)
    FT_HOME                 — freqtrade base directory
"""

import argparse
import os
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE",
    os.path.join(FT_HOME, "secrets", "service-account.json"),
)

# ---------------------------------------------------------------------------
# Sheet columns (must match export_to_sheets.py)
# ---------------------------------------------------------------------------

SHEET_COLUMNS = [
    "Date", "Pair", "Direction", "Entry", "Exit",
    "Stake", "P&L USDT", "P&L %", "Duration", "Strategy", "Exit Reason",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ---------------------------------------------------------------------------
# Dashboard layout constants
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


# ---------------------------------------------------------------------------
# Dashboard setup
# ---------------------------------------------------------------------------

def create_dashboard(sh: gspread.Spreadsheet) -> gspread.Worksheet:
    """Create and format the Dashboard worksheet."""
    dash = sh.add_worksheet(title="Dashboard", rows=100, cols=10)

    # ------ Header (rows 1-2) ------
    dash.merge_cells("A1:G1")
    dash.update("A1", [["TrendRider  --  Live P&L Tracker"]], value_input_option="USER_ENTERED")
    dash.format("A1:G1", {
        "textFormat": {"bold": True, "fontSize": 16},
        "horizontalAlignment": "CENTER",
        "backgroundColor": {"red": 0.11, "green": 0.11, "blue": 0.14},
    })

    dash.merge_cells("A2:G2")
    dash.update("A2", [["Updated every 6 hours  |  View only"]], value_input_option="USER_ENTERED")
    dash.format("A2:G2", {
        "textFormat": {"italic": True, "fontSize": 10, "foregroundColor": {"red": 0.6, "green": 0.6, "blue": 0.6}},
        "horizontalAlignment": "CENTER",
        "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95},
    })

    # ------ Key Metrics section header (row 4) ------
    dash.merge_cells("A4:B4")
    dash.update("A4", [["KEY METRICS"]], value_input_option="USER_ENTERED")
    dash.format("A4:B4", {
        "textFormat": {"bold": True, "fontSize": 12},
        "backgroundColor": {"red": 0.18, "green": 0.46, "blue": 0.82},
        "horizontalAlignment": "LEFT",
    })

    # ------ Metric labels (rows 5-14) ------
    label_cells = [[label] for label in DASHBOARD_METRIC_LABELS]
    dash.update(f"A5:A{5 + len(DASHBOARD_METRIC_LABELS) - 1}", label_cells, value_input_option="USER_ENTERED")

    # Placeholder dashes in value column
    dash.update(
        f"B5:B{5 + len(DASHBOARD_METRIC_LABELS) - 1}",
        [["--"] for _ in DASHBOARD_METRIC_LABELS],
        value_input_option="USER_ENTERED",
    )

    # Format label column: bold
    dash.format(f"A5:A{5 + len(DASHBOARD_METRIC_LABELS) - 1}", {
        "textFormat": {"bold": True, "fontSize": 10},
    })

    # Format value column: right-align
    dash.format(f"B5:B{5 + len(DASHBOARD_METRIC_LABELS) - 1}", {
        "textFormat": {"fontSize": 11},
        "horizontalAlignment": "RIGHT",
    })

    # ------ Monthly Breakdown section header ------
    monthly_start_row = 5 + len(DASHBOARD_METRIC_LABELS) + 2  # row 17
    dash.merge_cells(f"A{monthly_start_row}:G{monthly_start_row}")
    dash.update(
        f"A{monthly_start_row}",
        [["MONTHLY BREAKDOWN"]],
        value_input_option="USER_ENTERED",
    )
    dash.format(f"A{monthly_start_row}:G{monthly_start_row}", {
        "textFormat": {"bold": True, "fontSize": 12},
        "backgroundColor": {"red": 0.18, "green": 0.46, "blue": 0.82},
        "horizontalAlignment": "LEFT",
    })

    # Monthly table headers (row 18)
    header_row = monthly_start_row + 1
    dash.update(
        f"A{header_row}:G{header_row}",
        [MONTHLY_HEADERS],
        value_input_option="USER_ENTERED",
    )
    dash.format(f"A{header_row}:G{header_row}", {
        "textFormat": {"bold": True, "fontSize": 10},
        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
        "horizontalAlignment": "CENTER",
    })

    # ------ Column widths ------
    col_widths = [
        (0, 200),  # A — labels / Month
        (1, 130),  # B — values / Trades
        (2, 80),   # C — Wins
        (3, 80),   # D — Losses
        (4, 80),   # E — Win%
        (5, 110),  # F — P&L USDT
        (6, 90),   # G — P&L %
    ]
    requests_body = []
    for col_idx, width in col_widths:
        requests_body.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": dash.id,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })
    if requests_body:
        sh.batch_update({"requests": requests_body})

    # Freeze first 3 rows (header area)
    dash.freeze(rows=3)

    return dash


def setup_trades_sheet(sh: gspread.Spreadsheet) -> gspread.Worksheet:
    """Set up the Trades worksheet with headers and formatting."""
    ws = sh.sheet1
    ws.update_title("Trades")
    ws.append_row(SHEET_COLUMNS, value_input_option="USER_ENTERED")

    # Format header row: bold + freeze
    ws.format("A1:K1", {"textFormat": {"bold": True}})
    ws.freeze(rows=1)

    # Column widths
    column_widths = [
        ("A", 170),  # Date
        ("B", 130),  # Pair
        ("C", 80),   # Direction
        ("D", 110),  # Entry
        ("E", 110),  # Exit
        ("F", 80),   # Stake
        ("G", 90),   # P&L USDT
        ("H", 70),   # P&L %
        ("I", 80),   # Duration
        ("J", 140),  # Strategy
        ("K", 120),  # Exit Reason
    ]
    requests_body = []
    for col_letter, width in column_widths:
        col_idx = ord(col_letter) - ord("A")
        requests_body.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": ws.id,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })
    if requests_body:
        sh.batch_update({"requests": requests_body})

    return ws


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Google Sheet for trade exports")
    parser.add_argument("--name", default="Freqtrade Trades", help="Spreadsheet name")
    args = parser.parse_args()

    if not Path(CREDENTIALS_FILE).exists():
        print(f"ERROR: Service account credentials not found: {CREDENTIALS_FILE}")
        print("Place your service-account.json there or set GOOGLE_CREDENTIALS_FILE.")
        return

    # Authenticate
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)

    # Create spreadsheet
    print(f"Creating spreadsheet: {args.name}")
    sh = gc.create(args.name)

    # 1. Set up Trades sheet (uses default sheet1)
    print("Setting up Trades worksheet...")
    setup_trades_sheet(sh)

    # 2. Create Dashboard sheet and move it to position 0 (first tab)
    print("Creating Dashboard worksheet...")
    dash = create_dashboard(sh)

    # Move Dashboard to first position
    sh.batch_update({"requests": [{
        "updateSheetProperties": {
            "properties": {"sheetId": dash.id, "index": 0},
            "fields": "index",
        }
    }]})

    # Make public (read-only)
    sh.share("", perm_type="anyone", role="reader")
    print("Spreadsheet set to public (read-only).")

    # Output
    spreadsheet_id = sh.id
    spreadsheet_url = sh.url

    print()
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print(f"  Spreadsheet ID:  {spreadsheet_id}")
    print(f"  URL:             {spreadsheet_url}")
    print("  Worksheets:      Dashboard (summary) + Trades (raw data)")
    print()
    print("Next steps:")
    print(f'  1. Set env var:  export GOOGLE_SHEETS_ID="{spreadsheet_id}"')
    print("  2. Run:          python export_to_sheets.py --full")
    print("=" * 60)


if __name__ == "__main__":
    main()
