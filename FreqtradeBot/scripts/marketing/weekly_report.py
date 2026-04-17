#!/usr/bin/env python3
"""Weekly SEO/growth report — aggregates GSC + GitHub + Dev.to + HN + Pro Pack.

Runs Sunday 18:00 MSK, pings Telegram with a compact Russian summary plus
week-over-week deltas. Helps answer "идём в топ или стоим" без ручных
dashboards.

Cron:
    0 15 * * 0 . /etc/freqtrade.env && /usr/bin/python3 /opt/freqtrade/scripts/marketing/weekly_report.py

Environment:
    COMPOSIO_API_KEY, TG_TOKEN, ADMIN_CHAT_ID, GITHUB_TOKEN (optional)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

SITE_URL = "https://trendrider.net/"
REPO = "darkvolg/trendrider-strategy"
HN_ITEM_ID = 47803765
DEVTO_USERNAME = "trendrider"

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"
TG_TOKEN = os.environ.get("TG_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

STATE_FILE = Path("/var/lib/weekly_report_state.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("weekly_report")


def _composio(tool_slug: str, arguments: dict) -> dict | None:
    if not COMPOSIO_API_KEY:
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


def gsc_totals(start: str, end: str) -> dict:
    """Return {clicks, impressions, ctr, position} for a date range."""
    resp = _composio("GOOGLE_SEARCH_CONSOLE_SEARCH_ANALYTICS_QUERY", {
        "site_url": SITE_URL,
        "start_date": start,
        "end_date": end,
        "dimensions": [],
        "row_limit": 1,
    })
    data = _extract(resp)
    if not data:
        return {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0}
    rows = data.get("rows", []) if isinstance(data, dict) else []
    if not rows:
        return {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0}
    r = rows[0]
    return {
        "clicks": r.get("clicks", 0),
        "impressions": r.get("impressions", 0),
        "ctr": round(r.get("ctr", 0) * 100, 2),
        "position": round(r.get("position", 0), 1),
    }


def gsc_top_queries(start: str, end: str, limit: int = 5) -> list:
    resp = _composio("GOOGLE_SEARCH_CONSOLE_SEARCH_ANALYTICS_QUERY", {
        "site_url": SITE_URL,
        "start_date": start,
        "end_date": end,
        "dimensions": ["query"],
        "row_limit": limit,
    })
    data = _extract(resp)
    if not data:
        return []
    rows = data.get("rows", []) if isinstance(data, dict) else []
    return [
        {
            "query": r["keys"][0] if r.get("keys") else "?",
            "clicks": r.get("clicks", 0),
            "impr": r.get("impressions", 0),
            "pos": round(r.get("position", 0), 1),
        }
        for r in rows
    ]


def github_stats() -> dict:
    """Fetch repo stars/forks via unauthenticated GitHub REST API (60 req/hr)."""
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        r = requests.get(f"https://api.github.com/repos/{REPO}",
                         headers=headers, timeout=15)
        r.raise_for_status()
        d = r.json()
        return {
            "stargazerCount": d.get("stargazers_count", 0),
            "forkCount": d.get("forks_count", 0),
            "watchers": d.get("subscribers_count", 0),
        }
    except requests.RequestException as e:
        log.error("GitHub API failed: %s", e)
        return {"stargazerCount": 0, "forkCount": 0, "watchers": 0}


def devto_stats() -> dict:
    """Aggregate reactions/comments across recent articles.

    Dev.to public API does not expose page_views_count to non-owners, so we
    rely on public_reactions_count + comments_count + article count. Paginates
    up to 3 pages (~90 articles) to avoid Composio data_preview truncation.
    """
    totals = {"articles": 0, "reactions": 0, "comments": 0}
    for page in range(1, 4):
        resp = _composio("DEVTO_LIST_ARTICLES", {
            "username": DEVTO_USERNAME,
            "per_page": 30,
            "page": page,
        })
        data = _extract(resp)
        if not isinstance(data, dict):
            break
        items = data.get("articles") or data.get("data") or []
        if not isinstance(items, list) or not items:
            break
        dict_items = [i for i in items if isinstance(i, dict)]
        if not dict_items:
            break
        totals["articles"] += len(dict_items)
        totals["reactions"] += sum(i.get("public_reactions_count", 0) for i in dict_items)
        totals["comments"] += sum(i.get("comments_count", 0) for i in dict_items)
        if len(dict_items) < 30:
            break
    return totals


def hn_status() -> dict:
    try:
        r = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{HN_ITEM_ID}.json",
            timeout=10,
        )
        item = r.json() if r.ok else {}
        r2 = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10,
        )
        ids = r2.json() if r2.ok else []
        rank = ids.index(HN_ITEM_ID) + 1 if HN_ITEM_ID in ids[:200] else None
        return {
            "score": item.get("score", 0),
            "comments": item.get("descendants", 0),
            "rank": rank,
        }
    except requests.RequestException:
        return {"score": 0, "comments": 0, "rank": None}


def pro_pack_sales_week() -> int:
    """Count 'New sale' entries in pro_pack_sales.log from the last 7 days."""
    log_path = Path("/var/log/pro_pack_sales.log")
    if not log_path.exists():
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    try:
        lines = log_path.read_text().splitlines()
    except OSError:
        return 0
    count = 0
    for line in lines:
        if "[INFO] New sale" not in line and "New sale detected" not in line:
            continue
        # naive date parse "2026-04-17 ..." at start of line
        try:
            ts = datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                count += 1
        except ValueError:
            continue
    return count


def pr_statuses() -> dict:
    """Parse pr_monitor state (if JSON) or default to 0-count."""
    state_path = Path("/var/lib/pr_monitor_state.json")
    if not state_path.exists():
        return {"open": 0, "merged_this_week": 0}
    try:
        data = json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"open": 0, "merged_this_week": 0}
    statuses = data.get("statuses") or {}
    open_n = sum(1 for v in statuses.values() if v == "OPEN")
    merged_n = sum(1 for v in statuses.values() if v == "MERGED")
    return {"open": open_n, "merged_total": merged_n}


def load_prev() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(d: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    except OSError as e:
        log.error("save state failed: %s", e)


def fmt_delta(curr: float, prev: float | None, suffix: str = "") -> str:
    if prev is None:
        return f"{curr}{suffix}"
    delta = curr - prev
    sign = "+" if delta >= 0 else ""
    return f"{curr}{suffix} ({sign}{round(delta, 2)}{suffix})"


def main() -> int:
    today = datetime.now(timezone.utc).date()
    end = today - timedelta(days=3)   # GSC lags 2-3 days; use d-3 as end
    start = end - timedelta(days=6)   # 7-day window
    start_s, end_s = start.isoformat(), end.isoformat()

    log.info("GSC window: %s → %s", start_s, end_s)

    gsc = gsc_totals(start_s, end_s)
    top_q = gsc_top_queries(start_s, end_s, limit=5)
    gh = github_stats()
    dt = devto_stats()
    hn = hn_status()
    sales = pro_pack_sales_week()
    prs = pr_statuses()

    prev = load_prev()
    prev_gsc = prev.get("gsc", {})
    prev_gh = prev.get("gh", {})
    prev_dt = prev.get("dt", {})
    prev_hn = prev.get("hn", {})

    lines = [
        "📊 <b>TrendRider Weekly Report</b>",
        f"🗓 {start_s} → {end_s}",
        "",
        "<b>🔍 Google Search</b>",
        f"Clicks: {fmt_delta(gsc['clicks'], prev_gsc.get('clicks'))}",
        f"Impressions: {fmt_delta(gsc['impressions'], prev_gsc.get('impressions'))}",
        f"CTR: {fmt_delta(gsc['ctr'], prev_gsc.get('ctr'), '%')}",
        f"Avg position: {gsc['position']} (prev {prev_gsc.get('position','—')})",
    ]

    if top_q:
        lines.append("")
        lines.append("<b>Top queries (by clicks)</b>")
        for q in top_q:
            lines.append(f"• <i>{q['query'][:40]}</i> — {q['clicks']}c / {q['impr']}imp / pos {q['pos']}")

    lines.extend([
        "",
        f"<b>⭐ GitHub ({REPO})</b>",
        f"Stars: {fmt_delta(gh.get('stargazerCount',0), prev_gh.get('stargazerCount'))}",
        f"Forks: {fmt_delta(gh.get('forkCount',0), prev_gh.get('forkCount'))}",
        "",
        f"<b>📝 Dev.to (@{DEVTO_USERNAME})</b>",
        f"Articles: {dt['articles']}  •  Reactions: {fmt_delta(dt['reactions'], prev_dt.get('reactions'))}",
        f"Comments: {fmt_delta(dt['comments'], prev_dt.get('comments'))}",
        "",
        "<b>🚀 Show HN</b>",
        f"Score: {fmt_delta(hn['score'], prev_hn.get('score'))}  •  Comments: {hn['comments']}",
        f"Front page rank: {hn['rank'] or 'не на FP'}",
        "",
        f"<b>💰 Pro Pack sales (7d)</b>: {sales}",
        f"<b>📨 Outreach PRs</b>: open {prs.get('open',0)}, merged {prs.get('merged_total','—')}",
    ])

    text = "\n".join(lines)
    log.info("Report:\n%s", text)

    # Send to Telegram
    if TG_TOKEN and ADMIN_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={
                    "chat_id": ADMIN_CHAT_ID,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
        except requests.RequestException as e:
            log.error("Telegram send failed: %s", e)

    # Persist current snapshot for next week's delta
    save_state({
        "week": end_s,
        "gsc": gsc,
        "gh": gh,
        "dt": dt,
        "hn": hn,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
