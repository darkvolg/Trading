#!/usr/bin/env python3
"""One-time setup: create a Google Sheet for Freqtrade trade exports.

Creates a new spreadsheet, writes headers, makes it public (read-only),
and prints the spreadsheet ID + URL for use with export_to_sheets.py.

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

    # Write headers
    ws = sh.sheet1
    ws.update_title("Trades")
    ws.append_row(SHEET_COLUMNS, value_input_option="USER_ENTERED")

    # Format header row: bold + freeze
    ws.format("A1:K1", {"textFormat": {"bold": True}})
    ws.freeze(rows=1)

    # Auto-resize columns (set reasonable widths)
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
    print()
    print("Next steps:")
    print(f'  1. Set env var:  export GOOGLE_SHEETS_ID="{spreadsheet_id}"')
    print("  2. Run:          python export_to_sheets.py --full")
    print("=" * 60)


if __name__ == "__main__":
    main()
