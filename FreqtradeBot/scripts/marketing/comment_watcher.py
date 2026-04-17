#!/usr/bin/env python3
"""Dev.to comment watcher + GLM-drafted reply suggestions via Telegram.

Composio Dev.to has LIST_COMMENTS but no CREATE_COMMENT — so we detect new
comments and send drafted reply text to Telegram for the user to paste.
Still removes the "manual scan 47 articles daily" overhead.

Cron (daily at 11:30 MSK, 30 min after Dev.to publish):
    30 11 * * * /usr/bin/python3 /opt/freqtrade/scripts/marketing/comment_watcher.py

Environment:
    COMPOSIO_API_KEY      - for DEVTO_LIST_COMMENTS
    GLM_API_KEY/BASE/MODEL - for drafting replies
    TG_TOKEN / ADMIN_CHAT_ID - for notification
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
STATE_FILE = Path("/var/lib/comment_watcher_state.json")

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"
GLM_API_KEY = os.environ.get("GLM_API_KEY", "")
GLM_BASE_URL = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/anthropic")
GLM_MODEL = os.environ.get("GLM_MODEL", "glm-4.6")
TG_TOKEN = os.environ.get("TG_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

MAX_ARTICLES_SCAN = 10       # only poll the N most recent articles
MAX_REPLIES_PER_RUN = 5      # cap to avoid Telegram flood
OWN_USERNAME = "trendrider"  # skip comments authored by us

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("comment_watcher")


def _composio(tool_slug: str, arguments: dict) -> dict | None:
    """Execute a single Composio tool via the MCP HTTP endpoint."""
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
    """Unwrap the MCP envelope → Composio multi-execute → inner tool data."""
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


def fetch_comments(article_id: int) -> list:
    """Fetch all comments for a Dev.to article. Returns flat list (replies nested in 'children')."""
    resp = _composio("DEVTO_LIST_COMMENTS", {"a_id": article_id})
    data = _extract(resp)
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("comments", data.get("data", []))
    return []


def _flatten_comments(comments: list, parent_id: str | None = None) -> list[dict]:
    """Walk the nested comment tree → flat list with parent_id annotation."""
    out = []
    for c in comments:
        if not isinstance(c, dict):
            continue
        c = dict(c)
        c["_parent_id"] = parent_id
        out.append(c)
        children = c.get("children", [])
        if children:
            out.extend(_flatten_comments(children, parent_id=c.get("id_code")))
    return out


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"seen_ids": []}


def save_state(state: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    except OSError as e:
        log.error("Failed to save state: %s", e)


def load_recent_articles() -> list[dict]:
    """Fetch recent Dev.to articles by our username directly from Dev.to API."""
    resp = _composio("DEVTO_LIST_ARTICLES", {
        "username": OWN_USERNAME,
        "per_page": MAX_ARTICLES_SCAN,
        "page": 1,
    })
    data = _extract(resp)
    if not data:
        log.error("Failed to fetch Dev.to articles for @%s", OWN_USERNAME)
        return []

    items = data if isinstance(data, list) else data.get("articles", data.get("data", []))
    articles = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        articles.append({
            "slug": item.get("slug", ""),
            "devto_id": item.get("id"),
            "title": item.get("title", ""),
            "devto_url": item.get("url", ""),
            "comments_count": item.get("comments_count", 0),
        })
    return articles


def draft_reply(comment_body: str, article_title: str) -> str:
    """Ask GLM-4.6 to draft a short, human-sounding reply to a Dev.to comment."""
    if not GLM_API_KEY:
        return "[GLM_API_KEY missing — no draft generated]"

    system = (
        "You are the author of a Dev.to article about crypto algorithmic trading. "
        "A reader left a comment. Draft a SHORT (2-4 sentences), friendly, "
        "specific reply that acknowledges their point, adds one concrete piece "
        "of value (data, code hint, or experience), and does NOT sound robotic. "
        "No hashtags, no emojis unless the commenter used one. No sales pitch. "
        "If the comment is negative or spam, just write '[SKIP: negative/spam]'."
    )
    user = (
        f"Article: {article_title}\n\n"
        f"Reader comment:\n{comment_body.strip()[:1500]}\n\n"
        f"Draft your reply (plain markdown, no preamble):"
    )

    try:
        resp = requests.post(
            f"{GLM_BASE_URL}/v1/messages",
            headers={
                "x-api-key": GLM_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": GLM_MODEL,
                "max_tokens": 350,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        # Anthropic-compatible response: content[0].text
        content = data.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", "").strip()
        return data.get("output", "").strip() or "[empty GLM response]"
    except requests.RequestException as e:
        log.error("GLM draft failed: %s", e)
        return f"[GLM error: {e}]"


def notify_tg(text: str) -> None:
    if not TG_TOKEN or not ADMIN_CHAT_ID:
        log.warning("Telegram not configured; skipping notification")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": ADMIN_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        log.error("Telegram send failed: %s", e)


def main() -> int:
    articles = load_recent_articles()
    if not articles:
        log.info("No recent articles to scan")
        return 0

    state = load_state()
    seen: set = set(state.get("seen_ids", []))
    sent = 0

    for art in articles:
        devto_id = art.get("devto_id")
        if not devto_id:
            continue
        try:
            devto_id_int = int(devto_id)
        except (TypeError, ValueError):
            continue

        comments = fetch_comments(devto_id_int)
        if not comments:
            continue

        for c in _flatten_comments(comments):
            cid = c.get("id_code")
            if not cid or cid in seen:
                continue
            seen.add(cid)

            author = (c.get("user", {}) or {}).get("username", "unknown")
            if author == OWN_USERNAME:
                continue  # our own replies

            body = c.get("body_html", "") or c.get("body_markdown", "")
            # strip tags for draft
            import re
            clean = re.sub(r"<[^>]+>", "", body).strip()
            if len(clean) < 15:
                continue  # skip emoji-only / too-short

            draft = draft_reply(clean, art.get("title", ""))
            if draft.startswith("[SKIP:"):
                log.info("Skipping negative/spam comment %s", cid)
                continue

            devto_url = art.get("devto_url") or f"https://dev.to/{OWN_USERNAME}"
            # Escape HTML so Telegram parse_mode=HTML doesn't break
            from html import escape
            msg = (
                f"💬 <b>New Dev.to comment</b>\n"
                f"Article: {escape(art.get('title',''))[:80]}\n"
                f"By: @{escape(author)}\n\n"
                f"<b>Their comment:</b>\n<i>{escape(clean[:600])}</i>\n\n"
                f"<b>Draft reply (edit & paste):</b>\n{escape(draft)}\n\n"
                f"👉 <a href=\"{devto_url}\">Open article to reply</a>"
            )
            notify_tg(msg)
            sent += 1
            log.info("Drafted reply for %s by @%s", cid, author)
            if sent >= MAX_REPLIES_PER_RUN:
                break
        if sent >= MAX_REPLIES_PER_RUN:
            break

    state["seen_ids"] = sorted(seen)[-500:]  # keep last 500 ids only
    save_state(state)
    log.info("Done. %d new comments drafted this run.", sent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
