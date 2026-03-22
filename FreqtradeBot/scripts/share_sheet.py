#!/usr/bin/env python3
"""Share Google Sheet as public (view-only) and post link to Telegram.

Opens an existing spreadsheet, sets it to anyone-can-view, and sends
a formatted message to the Telegram channel with the direct link.

Usage:
    python share_sheet.py              # share + send to Telegram
    python share_sheet.py --dry-run    # only print the message, don't send

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
import sys
import urllib.request
import urllib.error
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# Paths (same pattern as export_to_sheets.py)
# ---------------------------------------------------------------------------

FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))
CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE",
    os.path.join(FT_HOME, "secrets", "service-account.json"),
)
SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ---------------------------------------------------------------------------
# Telegram config
# ---------------------------------------------------------------------------


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
# Google Sheets
# ---------------------------------------------------------------------------


def get_gspread_client() -> gspread.Client:
    """Authenticate via service account and return gspread client."""
    if not Path(CREDENTIALS_FILE).exists():
        raise FileNotFoundError(
            f"Service account credentials not found: {CREDENTIALS_FILE}\n"
            "Set GOOGLE_CREDENTIALS_FILE or place the JSON at the default path."
        )
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def share_sheet_public(spreadsheet_id: str) -> str:
    """Share sheet as view-only for anyone. Returns the sheet URL."""
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    sh.share(None, perm_type="anyone", role="reader")
    return sh.url


# ---------------------------------------------------------------------------
# Telegram (urllib-based)
# ---------------------------------------------------------------------------

MESSAGE_TEMPLATE = (
    "\U0001f4ca *TrendRider — Live P&L Tracker*\n"
    "\n"
    "Полная прозрачность наших результатов. Все сделки записываются автоматически.\n"
    "\n"
    "\U0001f517 [Открыть Google Sheet]({sheet_url})\n"
    "\n"
    "Обновляется каждые 6 часов.\n"
    "Колонки: Date, Pair, Direction, Entry, Exit, P&L %, Duration\n"
    "\n"
    "_Transparency is our edge._"
)


def build_message(sheet_url: str) -> str:
    """Build the Telegram message with the sheet URL."""
    return MESSAGE_TEMPLATE.format(sheet_url=sheet_url)


def send_telegram(text: str) -> None:
    """Send a Markdown message to Telegram using urllib."""
    token, chat_id = get_telegram_config()

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("Telegram message sent successfully.")
            else:
                print(f"Telegram API returned status {resp.status}.")
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Telegram HTTP error {e.code}: {e.reason}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"[ERROR] Telegram URL error: {e.reason}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Share Google Sheet as public and post link to Telegram"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the message without sending to Telegram",
    )
    args = parser.parse_args()

    # Validate config
    if not SHEETS_ID:
        print("ERROR: GOOGLE_SHEETS_ID env var is not set.")
        print("Run setup_sheets.py first to create a spreadsheet, then set the env var.")
        return

    # Share sheet as public
    try:
        print(f"Sharing spreadsheet {SHEETS_ID} as view-only...")
        sheet_url = share_sheet_public(SHEETS_ID)
        print(f"Sheet is now public: {sheet_url}")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return
    except Exception as e:
        print(f"[ERROR] Failed to share sheet: {e}", file=sys.stderr)
        return

    # Build message
    message = build_message(sheet_url)

    if args.dry_run:
        print("\n--- DRY RUN (message not sent) ---")
        print(message)
        print("--- END ---")
        return

    # Send to Telegram
    try:
        send_telegram(message)
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
