#!/usr/bin/env python3
"""Gmail auto-cleanup cron — Composio-filter workaround.

Composio's Gmail OAuth config lacks `gmail.settings.basic` scope, so
GMAIL_CREATE_FILTER returns 403. Workaround: every hour, query inbox for
known-noise senders and batch-trash. Same effect, 1-hour lag.

Cron (every hour at :17, offset from article_generator):
    17 * * * * /usr/bin/python3 /opt/freqtrade/scripts/marketing/gmail_autoclean.py

Environment:
    COMPOSIO_API_KEY - required
"""

from __future__ import annotations

import json
import logging
import os
import sys

import requests

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"

# Patterns to auto-trash. Each: (label, gmail-search-query)
# IMPORTANT: keep these narrow. Mis-trashing real business mail is bad.
CLEANUP_QUERIES = [
    ("LinkedIn notifications",     "in:inbox from:notifications@linkedin.com"),
    ("LinkedIn jobs",              "in:inbox from:jobs-noreply@linkedin.com"),
    ("Bybit marketing",            "in:inbox from:marketing@mail.bybit.com"),
    ("Bybit newsletter",           "in:inbox from:newsletter@mail.bybit.com"),
    ("Google Drive access req",    "in:inbox from:drive-shares-dm-noreply@google.com"),
    ("Category: promotions",       "in:inbox category:promotions"),
    ("Avito marketing",            "in:inbox from:collection@avito.ru"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("gmail_autoclean")


def _composio(tool_slug: str, arguments: dict) -> dict | None:
    if not COMPOSIO_API_KEY:
        log.error("COMPOSIO_API_KEY missing")
        return None
    payload = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {
            "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
            "arguments": {"tools": [{"tool_slug": tool_slug, "arguments": arguments}]},
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-CONSUMER-API-KEY": COMPOSIO_API_KEY,
    }
    try:
        resp = requests.post(COMPOSIO_MCP_URL, headers=headers, json=payload, timeout=60)
        raw = resp.text.strip()
        for line in reversed(raw.split("\n")):
            if line.startswith("data: "):
                return json.loads(line[6:])
        return json.loads(raw)
    except (requests.RequestException, json.JSONDecodeError) as e:
        log.error("Composio call failed (%s): %s", tool_slug, e)
        return None


def _extract(response: dict) -> dict | list | None:
    if not response:
        return None
    content = response.get("result", {}).get("content", [])
    for item in content:
        if item.get("type") != "text":
            continue
        try:
            parsed = json.loads(item["text"])
        except (json.JSONDecodeError, KeyError):
            continue
        if isinstance(parsed, dict) and "data" in parsed:
            results = parsed.get("data", {}).get("results", [])
            if results and isinstance(results, list):
                resp0 = results[0].get("response", {})
                inner = resp0.get("data") or resp0.get("data_preview") or {}
                if inner:
                    return inner
        return parsed
    return None


def fetch_ids(query: str, limit: int = 100) -> list[str]:
    resp = _composio("GMAIL_FETCH_EMAILS", {
        "query": query,
        "max_results": limit,
        "ids_only": True,
        "verbose": False,
        "include_payload": False,
    })
    data = _extract(resp)
    if not isinstance(data, dict):
        return []
    msgs = data.get("messages", []) or []
    return [m.get("messageId") or m.get("id") for m in msgs
            if isinstance(m, dict) and (m.get("messageId") or m.get("id"))]


def trash_ids(ids: list[str]) -> bool:
    if not ids:
        return True
    # Batch cap is 1000
    for i in range(0, len(ids), 1000):
        chunk = ids[i:i + 1000]
        resp = _composio("GMAIL_BATCH_MODIFY_MESSAGES", {
            "messageIds": chunk,
            "addLabelIds": ["TRASH"],
            "removeLabelIds": ["INBOX", "UNREAD"],
        })
        data = _extract(resp)
        if not data or not (isinstance(data, dict) and data.get("success", True)):
            log.error("Batch modify failed for chunk of %d ids: %s", len(chunk), data)
            return False
    return True


def main() -> int:
    total_trashed = 0
    for label, query in CLEANUP_QUERIES:
        ids = fetch_ids(query)
        if not ids:
            continue
        if trash_ids(ids):
            log.info("Trashed %d × %s", len(ids), label)
            total_trashed += len(ids)
        else:
            log.warning("Failed to trash %s (%d ids)", label, len(ids))
    log.info("Done. %d emails auto-cleaned this run.", total_trashed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
