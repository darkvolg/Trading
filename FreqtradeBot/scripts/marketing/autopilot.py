#!/usr/bin/env python3
"""
Marketing Autopilot — automated content posting for TrendRider.

Modes: --twitter, --reddit, --remind
Each mode is independent and designed to run via cron on a Linux server.

Cron:
    0 9,18 * * * /usr/bin/python3 /opt/freqtrade/scripts/marketing/autopilot.py --twitter
    0 14 * * * /usr/bin/python3 /opt/freqtrade/scripts/marketing/autopilot.py --reddit
    0 10 * * * /usr/bin/python3 /opt/freqtrade/scripts/marketing/autopilot.py --remind

Environment:
    TWITTER_CONSUMER_KEY      - Twitter API consumer key
    TWITTER_CONSUMER_SECRET   - Twitter API consumer secret
    TWITTER_ACCESS_TOKEN      - Twitter access token
    TWITTER_ACCESS_SECRET     - Twitter access token secret
    COMPOSIO_API_KEY          - Composio MCP API key for Reddit
    TG_TOKEN                  - Telegram bot token
    ADMIN_CHAT_ID             - Telegram admin chat ID for reminders
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote as urlquote

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
CONTENT_BANK_PATH = SCRIPT_DIR / "content_bank.json"
STATE_FILE = Path.home() / ".marketing_state.json"
LOG_DIR = Path.home() / "logs"
LOG_FILE = LOG_DIR / "marketing_autopilot.log"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("autopilot")

# ---------------------------------------------------------------------------
# Environment config
# ---------------------------------------------------------------------------
TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "")

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"

TG_TOKEN = os.environ.get("TG_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

# Reddit search keywords to match posts for commenting
REDDIT_KEYWORDS = [
    "freqtrade", "algo trading", "algotrading", "crypto bot",
    "trading bot", "automated trading", "backtesting", "bybit",
    "binance bot", "crypto strategy", "technical analysis bot",
    "quant trading", "systematic trading", "trend following",
]

REDDIT_SUBREDDIT = "algotrading"

BLOG_MANIFEST_PATH = SCRIPT_DIR / "blog_manifest.json"
SITE_URL = "https://trendrider.net"

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------


def load_state() -> dict:
    """Load posting state from JSON file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Failed to load state file, starting fresh: %s", e)
    return {
        "twitter_index": 0,
        "reddit_index": 0,
        "last_twitter": "",
        "last_reddit": "",
        "reminders_sent": {},
    }


def save_state(state: dict) -> None:
    """Persist state to JSON file."""
    try:
        STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as e:
        log.error("Failed to save state: %s", e)


def load_blog_manifest() -> list:
    """Load blog manifest JSON. Returns list of article dicts or empty list."""
    if not BLOG_MANIFEST_PATH.exists():
        log.error("Blog manifest not found at %s", BLOG_MANIFEST_PATH)
        return []
    try:
        data = json.loads(BLOG_MANIFEST_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        log.error("Blog manifest is not a JSON array")
        return []
    except (json.JSONDecodeError, OSError) as e:
        log.error("Failed to load blog manifest: %s", e)
        return []


def load_content_bank() -> dict:
    """Load content bank JSON. Returns empty structure on failure."""
    if not CONTENT_BANK_PATH.exists():
        log.error("Content bank not found at %s", CONTENT_BANK_PATH)
        return {"twitter_posts": [], "reddit_comments": [], "reminders": []}
    try:
        return json.loads(CONTENT_BANK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log.error("Failed to load content bank: %s", e)
        return {"twitter_posts": [], "reddit_comments": [], "reminders": []}


# ---------------------------------------------------------------------------
# Twitter OAuth 1.0a
# ---------------------------------------------------------------------------


def _percent_encode(s: str) -> str:
    """RFC 5849 percent-encode."""
    return urlquote(str(s), safe="")


def _generate_oauth_signature(
    method: str,
    url: str,
    params: dict,
    consumer_secret: str,
    token_secret: str,
) -> str:
    """Create OAuth 1.0a HMAC-SHA1 signature."""
    # Sort parameters and build parameter string
    sorted_params = sorted(params.items())
    param_string = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted_params
    )

    # Build signature base string
    base_string = "&".join([
        method.upper(),
        _percent_encode(url),
        _percent_encode(param_string),
    ])

    # Build signing key
    signing_key = f"{_percent_encode(consumer_secret)}&{_percent_encode(token_secret)}"

    # HMAC-SHA1
    hashed = hmac.new(
        signing_key.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha1,
    )
    return base64.b64encode(hashed.digest()).decode("utf-8")


def _build_oauth_header(method: str, url: str, body_params: dict | None = None) -> str:
    """Build the full OAuth Authorization header string."""
    oauth_params = {
        "oauth_consumer_key": TWITTER_CONSUMER_KEY,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": TWITTER_ACCESS_TOKEN,
        "oauth_version": "1.0",
    }

    # Combine oauth params with any body params for signing
    all_params = dict(oauth_params)
    if body_params:
        all_params.update(body_params)

    signature = _generate_oauth_signature(
        method, url, all_params,
        TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_SECRET,
    )
    oauth_params["oauth_signature"] = signature

    # Build header
    header_parts = ", ".join(
        f'{_percent_encode(k)}="{_percent_encode(v)}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {header_parts}"


def twitter_post(text: str) -> bool:
    """Post a tweet using Twitter API v2 with OAuth 1.0a."""
    if not all([TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
                TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        log.error("Twitter credentials not configured (env vars missing)")
        return False

    url = "https://api.twitter.com/2/tweets"
    # Twitter API v2 uses JSON body, not form-encoded params for signing
    auth_header = _build_oauth_header("POST", url)

    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }
    payload = {"text": text}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            data = resp.json()
            tweet_id = data.get("data", {}).get("id", "unknown")
            log.info("Tweet posted successfully (id=%s): %s", tweet_id, text[:80])
            return True
        else:
            log.error(
                "Twitter API error %d: %s",
                resp.status_code,
                resp.text[:500],
            )
            return False
    except requests.RequestException as e:
        log.error("Twitter request failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Reddit via Composio MCP
# ---------------------------------------------------------------------------


def _composio_mcp_call(tool_slug: str, arguments: dict) -> dict | None:
    """Execute a tool via Composio MCP endpoint. Returns parsed result or None."""
    if not COMPOSIO_API_KEY:
        log.error("COMPOSIO_API_KEY not configured")
        return None

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {
            "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
            "arguments": {
                "tools": [{"tool_slug": tool_slug, "arguments": arguments}],
            },
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-CONSUMER-API-KEY": COMPOSIO_API_KEY,
    }

    try:
        resp = requests.post(
            COMPOSIO_MCP_URL, headers=headers,
            json=payload, timeout=60,
        )
        raw = resp.text.strip()

        # MCP returns SSE format — extract last JSON data line
        lines = raw.split("\n")
        for line in reversed(lines):
            if line.startswith("data: "):
                return json.loads(line[6:])
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

        return json.loads(raw)
    except (requests.RequestException, json.JSONDecodeError) as e:
        log.error("Composio MCP call failed (%s): %s", tool_slug, e)
        return None


def _extract_composio_result(response: dict) -> dict | list | None:
    """Extract actual data from MCP response envelope."""
    if not response:
        return None
    result = response.get("result", {})
    content = result.get("content", [])
    for item in content:
        if item.get("type") == "text":
            try:
                parsed = json.loads(item["text"])
                # Unwrap Composio multi-execute envelope
                if isinstance(parsed, dict) and "data" in parsed:
                    results = parsed.get("data", {}).get("results", [])
                    if results and isinstance(results, list):
                        resp0 = results[0].get("response", {})
                        inner = resp0.get("data") or resp0.get("data_preview") or {}
                        if inner:
                            return inner
                return parsed
            except (json.JSONDecodeError, KeyError):
                return item
    return result


def _fetch_recent_posts(subreddit: str, sort: str = "new", limit: int = 20) -> list:
    """Fetch recent posts from a subreddit via Composio.

    Uses REDDIT_RETRIEVE_REDDIT_POST (per-subreddit fetch) instead of the
    cross-sub search endpoint, which had a ~50% miss rate on r/algotrading.
    Response shape: {kind: "Listing", data: {children: [{data: {...}, kind: "t3"}, ...]}}
    """
    resp = _composio_mcp_call("REDDIT_RETRIEVE_REDDIT_POST", {
        "subreddit": subreddit,
        "sort": sort,
        "max_results": min(limit, 100),
    })
    data = _extract_composio_result(resp)
    if not data:
        return []

    if isinstance(data, dict):
        inner = data.get("data", data)
        children = inner.get("children", []) if isinstance(inner, dict) else []
        return children if isinstance(children, list) else []
    if isinstance(data, list):
        return data
    return []


def _pick_matching_post(posts: list, keywords: list[str]) -> dict | None:
    """Find the first post whose title or body matches any keyword."""
    for post in posts:
        if not isinstance(post, dict):
            continue
        p = post.get("data", post)
        title = (p.get("title", "") or "").lower()
        body = (p.get("selftext", "") or "").lower()
        combined = f"{title} {body}"

        for kw in keywords:
            if kw.lower() in combined:
                return p

    return None


def reddit_comment(comment_text: str) -> bool:
    """Search for a matching post in r/algotrading and post a comment."""
    log.info("Fetching recent posts from r/%s...", REDDIT_SUBREDDIT)
    posts = _fetch_recent_posts(REDDIT_SUBREDDIT, sort="new", limit=25)
    if not posts:
        log.warning("No posts fetched from r/%s, trying hot...", REDDIT_SUBREDDIT)
        posts = _fetch_recent_posts(REDDIT_SUBREDDIT, sort="hot", limit=25)

    if not posts:
        log.error("Could not fetch any posts from r/%s", REDDIT_SUBREDDIT)
        return False

    # Strict filter: only real in-sub posts, no cross-sub fallback
    in_sub = []
    for _post in posts:
        if not isinstance(_post, dict):
            continue
        _p = _post.get("data", _post)
        if not isinstance(_p, dict):
            continue
        if (_p.get("subreddit", "") or "").lower() == REDDIT_SUBREDDIT.lower():
            in_sub.append(_p)
    matched = _pick_matching_post(in_sub, REDDIT_KEYWORDS)
    if not matched:
        log.warning("No r/%s posts matched (%d in-sub checked). Skipping.", REDDIT_SUBREDDIT, len(in_sub))
        return False

    post_id = matched.get("id", matched.get("name", ""))
    post_title = matched.get("title", "?")

    # Ensure t3_ prefix
    thing_id = post_id if post_id.startswith("t3_") else f"t3_{post_id}"

    log.info("Commenting on post '%s' (id=%s)", post_title[:60], thing_id)

    resp = _composio_mcp_call("REDDIT_POST_REDDIT_COMMENT", {
        "thing_id": thing_id,
        "text": comment_text,
    })
    data = _extract_composio_result(resp)
    if not data:
        log.error("Empty response from Reddit comment API")
        return False

    data_str = json.dumps(data)

    # Check rate limit
    if "rate limit" in data_str.lower() or "take a break" in data_str.lower():
        match = re.search(r"(\d+)\s*minute", data_str)
        wait_min = int(match.group(1)) if match else 10
        log.warning("Reddit rate limited, need to wait ~%d minutes", wait_min)
        return False

    log.info("Reddit comment posted successfully")

    # Try to extract permalink
    try:
        things = data.get("data", {}).get("json", {}).get("data", {}).get("things", [])
        if things:
            permalink = things[0].get("data", {}).get("permalink", "")
            if permalink:
                log.info("Comment URL: https://www.reddit.com%s", permalink)
    except (KeyError, IndexError, TypeError, AttributeError):
        pass

    return True


# ---------------------------------------------------------------------------
# Telegram reminders
# ---------------------------------------------------------------------------

DAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def _send_telegram(text: str) -> bool:
    """Send a Telegram message to admin."""
    if not TG_TOKEN or not ADMIN_CHAT_ID:
        log.error("TG_TOKEN or ADMIN_CHAT_ID not configured")
        return False

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            log.info("Telegram reminder sent: %s", text[:80])
            return True
        else:
            log.error("Telegram API error %d: %s", resp.status_code, resp.text[:300])
            return False
    except requests.RequestException as e:
        log.error("Telegram request failed: %s", e)
        return False


def send_reminders(state: dict, content_bank: dict) -> dict:
    """Check and send all due reminders. Returns updated state."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    weekday = now.weekday()  # 0=Monday

    reminders_sent = state.get("reminders_sent", {})
    all_reminders = content_bank.get("reminders", [])

    for reminder in all_reminders:
        rtext = reminder.get("text", "")
        rid = reminder.get("id", "unknown")
        rdate = reminder.get("date", "")
        recurring = reminder.get("recurring", "")

        if not rtext:
            continue

        if recurring:
            # --- Recurring reminders ---
            if recurring == "daily":
                key = f"recurring_{rid}_{today_str}"
                if key not in reminders_sent:
                    prefix = "\U0001f4cb <b>Ежедневное напоминание</b>\n\n"
                    if _send_telegram(prefix + rtext):
                        reminders_sent[key] = True
            elif recurring == "1st":
                if now.day == 1:
                    key = f"recurring_{rid}_{today_str}"
                    if key not in reminders_sent:
                        prefix = "\U0001f4ca <b>Месячное напоминание</b>\n\n"
                        if _send_telegram(prefix + rtext):
                            reminders_sent[key] = True
            elif recurring.lower() in DAY_MAP:
                if weekday == DAY_MAP[recurring.lower()]:
                    key = f"recurring_{rid}_{today_str}"
                    if key not in reminders_sent:
                        prefix = "\U0001f4cb <b>Еженедельное напоминание</b>\n\n"
                        if _send_telegram(prefix + rtext):
                            reminders_sent[key] = True
        elif rdate:
            # --- Date-based reminders ---
            try:
                reminder_date = datetime.strptime(rdate, "%Y-%m-%d").date()
            except ValueError:
                log.warning("Invalid reminder date format: %s", rdate)
                continue

            if now.date() >= reminder_date:
                key = f"dated_{rid}"
                if key not in reminders_sent:
                    prefix = "\U0001f514 <b>Запланированное напоминание</b>\n\n"
                    if _send_telegram(prefix + rtext):
                        reminders_sent[key] = True

    state["reminders_sent"] = reminders_sent
    return state


# ---------------------------------------------------------------------------
# Mode handlers
# ---------------------------------------------------------------------------


LIVE_STATS_PATH = Path("/var/www/trendrider/api/live-stats.json")


def build_live_stats_tweet() -> str | None:
    """Build a build-in-public tweet from /live stats JSON. Returns None on failure."""
    try:
        data = json.loads(LIVE_STATS_PATH.read_text())
    except Exception as e:
        log.warning("Live stats read failed: %s", e)
        return None

    try:
        balance = data["current_balance"]
        pnl_abs = data["pnl_abs"]
        pnl_pct = data["pnl_pct"]
        wr = data["win_rate_pct"]
        wins = data["wins"]
        losses = data["losses"]
        closed = data["closed_trades"]
        first = data.get("first_trade_date", "")

        # Day counter since first trade
        days = ""
        if first:
            try:
                first_dt = datetime.fromisoformat(first.replace(" ", "T")[:19])
                days_n = (datetime.now(timezone.utc).replace(tzinfo=None) - first_dt).days
                days = f" — Day {days_n}" if days_n > 0 else ""
            except Exception:
                pass

        # Exit breakdown: find best and worst
        breakdown = data.get("exit_breakdown", [])
        best = max(breakdown, key=lambda e: e["total_abs"], default=None)
        worst = min(breakdown, key=lambda e: e["total_abs"], default=None)

        sign = "+" if pnl_abs >= 0 else ""
        lines = [
            f"📊 TrendRider bot{days}",
            "",
            f"Balance: ${balance:.2f} ({sign}{pnl_pct:.2f}%)",
            f"WR: {wr:.1f}% ({wins}W/{losses}L, {closed} trades)",
        ]
        if best and best["total_abs"] > 0:
            lines.append(f"Best exit: {best['exit_reason']} +${best['total_abs']:.2f}")
        if worst and worst["total_abs"] < 0:
            lines.append(f"Worst exit: {worst['exit_reason']} -${abs(worst['total_abs']):.2f}")
        lines += [
            "",
            "Raw sqlite, no filter:",
            "https://trendrider.net/live",
            "",
            "⭐ github.com/darkvolg/trendrider-strategy",
            "",
            "#freqtrade #algotrading",
        ]
        tweet = "\n".join(lines)
        if len(tweet) > 280:
            # Drop best/worst lines if too long
            tweet = "\n".join([lines[0], "", lines[2], lines[3], "", "https://trendrider.net/live", "", "⭐ github.com/darkvolg/trendrider-strategy"])
        return tweet
    except Exception as e:
        log.error("Live stats tweet build failed: %s", e)
        return None


def handle_twitter(state: dict, content_bank: dict) -> dict:
    """Post tweet: prefer live bot stats (build-in-public), fall back to static rotation."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last = state.get("last_twitter", "")
    today_count = state.get("twitter_today_count", 0)
    if last == today_str and today_count >= 2:
        log.info("Already posted 2 tweets today (%s), skipping", today_str)
        return state
    if last != today_str:
        today_count = 0

    # Try live stats first (Proof-of-Income strategy)
    live_tweet = build_live_stats_tweet()
    if live_tweet:
        log.info("Posting live stats tweet (%d chars): %s", len(live_tweet), live_tweet[:100])
        if twitter_post(live_tweet):
            state["last_twitter"] = today_str
            state["twitter_today_count"] = today_count + 1
            log.info("Live stats tweet posted successfully")
            return state
        log.error("Live stats tweet failed, falling back to static rotation")

    # Fallback: static rotation from content bank
    tweets = content_bank.get("twitter_posts", [])
    if not tweets:
        log.error("No twitter_posts in content bank and live stats unavailable")
        return state

    idx = state.get("twitter_index", 0) % len(tweets)
    tweet_obj = tweets[idx]
    tweet_text = tweet_obj["text"] if isinstance(tweet_obj, dict) else str(tweet_obj)

    log.info("Posting static tweet #%d (of %d): %s", idx + 1, len(tweets), tweet_text[:80])

    if twitter_post(tweet_text):
        state["twitter_index"] = (idx + 1) % len(tweets)
        state["last_twitter"] = today_str
        state["twitter_today_count"] = today_count + 1
    else:
        log.error("Tweet posting failed, index stays at %d", idx)

    return state


def handle_reddit(state: dict, content_bank: dict) -> dict:
    """Post next Reddit comment from content bank."""
    comments = content_bank.get("reddit_comments", [])
    if not comments:
        log.error("No reddit_comments in content bank")
        return state

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_reddit") == today_str:
        log.info("Already posted a Reddit comment today (%s), skipping", today_str)
        return state

    idx = state.get("reddit_index", 0) % len(comments)
    comment_obj = comments[idx]
    comment_text = comment_obj["text"] if isinstance(comment_obj, dict) else str(comment_obj)

    log.info(
        "Posting Reddit comment #%d (of %d): %s",
        idx + 1, len(comments), comment_text[:80],
    )

    if reddit_comment(comment_text):
        state["reddit_index"] = (idx + 1) % len(comments)
        state["last_reddit"] = today_str
        log.info("Reddit index advanced to %d", state["reddit_index"])
    else:
        log.error("Reddit comment posting failed, index stays at %d", idx)

    return state


def handle_remind(state: dict, content_bank: dict) -> dict:
    """Process and send due reminders."""
    return send_reminders(state, content_bank)


def handle_devto(state: dict, content_bank: dict) -> dict:
    """Publish next blog article to Dev.to from blog manifest."""
    manifest = load_blog_manifest()
    if not manifest:
        log.error("Blog manifest is empty, nothing to publish")
        return state

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if state.get("last_devto") == today_str:
        log.info("Already published to Dev.to today (%s), skipping", today_str)
        return state

    published = state.get("devto_published", [])
    article = None
    for entry in manifest:
        if entry["slug"] not in published:
            article = entry
            break

    if article is None:
        log.info("All %d blog articles already published to Dev.to", len(manifest))
        return state

    slug = article["slug"]
    title = article["title"]
    summary = article["summary"]
    tags = article.get("tags", [])[:4]
    canonical_url = f"{SITE_URL}/blog/{slug}"

    body_markdown = (
        f"*Originally published at [trendrider.net]({canonical_url})*\n\n"
        f"# {title}\n\n"
        f"{summary}\n\n"
        f"## Key Takeaways\n\n"
        f"This article covers {summary[0].lower() + summary[1:]} "
        f"Read the full analysis with charts, data tables, and real backtest results.\n\n"
        f"**[Read the full article on TrendRider →]({canonical_url})**\n\n"
        f"---\n\n"
        f"*TrendRider AI is a free algorithmic crypto trading system with 67.9% "
        f"backtested win rate. [Join our Telegram](https://t.me/trendrider_signals) "
        f"for free signals.*\n\n"
        f"---\n\n"
        f"**Did you find this useful?** Hit the ❤️ button and drop a comment — "
        f"I'd love to hear what strategies you're running or what topics "
        f"you want me to cover next!"
    )

    log.info("Publishing to Dev.to: '%s' (slug=%s)", title, slug)

    resp = _composio_mcp_call("DEVTO_CREATE_ARTICLE", {
        "title": title,
        "body_markdown": body_markdown,
        "tags": tags,
        "published": True,
        "canonical_url": canonical_url,
    })
    data = _extract_composio_result(resp)

    if data and isinstance(data, dict) and data.get("id"):
        devto_url = data.get("url", data.get("canonical_url", ""))
        log.info("Dev.to article published: %s (id=%s)", devto_url, data.get("id"))
        published.append(slug)
        state["devto_published"] = published
        state["last_devto"] = today_str
        _send_telegram(
            f"\u2705 Dev.to: опубликована статья '{title}'\n{devto_url}"
        )
    else:
        log.error("Dev.to publish failed for '%s': %s", title, data)
        _send_telegram(f"\u274c Dev.to: ошибка публикации '{title}'")

    return state



def handle_hashnode(state: dict, content_bank: dict) -> dict:
    """Publish next blog article to Hashnode from blog manifest (direct GraphQL API)."""
    token = os.environ.get("HASHNODE_TOKEN", "")
    pub_id = os.environ.get("HASHNODE_PUBLICATION_ID", "")
    if not token or not pub_id:
        log.error("HASHNODE_TOKEN or HASHNODE_PUBLICATION_ID missing")
        return state

    manifest = load_blog_manifest()
    if not manifest:
        log.error("Blog manifest is empty, nothing to publish")
        return state

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_hashnode") == today_str:
        log.info("Already published to Hashnode today (%s), skipping", today_str)
        return state

    published = state.get("hashnode_published", [])
    article = None
    for entry in manifest:
        if entry["slug"] not in published:
            article = entry
            break
    if article is None:
        log.info("All %d blog articles already published to Hashnode", len(manifest))
        return state

    slug = article["slug"]
    title = article["title"]
    summary = article["summary"]
    tags = article.get("tags", [])[:5]
    canonical_url = f"{SITE_URL}/blog/{slug}"
    # Auto-detect hero image extension from filesystem (.webp, .png, .jpg)
    heroes_dir = Path("/var/www/trendrider/blog-heroes")
    cover_url = None
    for ext in (".webp", ".png", ".jpg", ".jpeg"):
        if (heroes_dir / f"{slug}{ext}").exists():
            cover_url = f"{SITE_URL}/blog-heroes/{slug}{ext}"
            break
    if not cover_url:
        log.warning("No hero image found for %s, publishing without cover", slug)

    content_md = (
        f"> *Originally published at [trendrider.net]({canonical_url})*\n\n"
        f"{summary}\n\n"
        f"## What You Will Learn\n\n"
        f"This article breaks down the complete strategy with real backtest data, "
        f"exact entry/exit rules, and Python code examples you can run today.\n\n"
        f"**[Read the full article on TrendRider \u2192]({canonical_url})**\n\n"
        f"---\n\n"
        f"TrendRider is a free algorithmic crypto trading system with 67.9% "
        f"backtested win rate. [Join Telegram](https://t.me/trendrider_signals) "
        f"for free signals, or check the [live dashboard]({SITE_URL})."
    )

    tags_input = [{"slug": t.lower().replace(" ", "-"), "name": t} for t in tags]

    mutation = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) {
        post { id url slug }
      }
    }
    """
    input_data = {
        "publicationId": pub_id,
        "title": title,
        "contentMarkdown": content_md,
        "slug": slug,
        "tags": tags_input,
        "originalArticleURL": canonical_url,
    }
    if cover_url:
        input_data["coverImageOptions"] = {"coverImageURL": cover_url}
    variables = {"input": input_data}

    log.info("Publishing to Hashnode: %s (slug=%s)", title, slug)
    try:
        resp = requests.post(
            "https://gql.hashnode.com/",
            headers={"Authorization": token, "Content-Type": "application/json"},
            json={"query": mutation, "variables": variables},
            timeout=60,
        )
        data = resp.json()
        if "errors" in data:
            log.error("Hashnode publish failed: %s", data["errors"])
            _send_telegram(f"\u274c Hashnode: \u043e\u0448\u0438\u0431\u043a\u0430 '{title}'")
            return state
        post = data.get("data", {}).get("publishPost", {}).get("post", {})
        post_url = post.get("url", "")
        log.info("Hashnode published: %s (id=%s)", post_url, post.get("id"))
        published.append(slug)
        state["hashnode_published"] = published
        state["last_hashnode"] = today_str
        _send_telegram(f"\u2705 Hashnode: \u043e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u0430 '{title}'\n{post_url}")
    except Exception as e:
        log.exception("Hashnode publish exception")
        _send_telegram(f"\u274c Hashnode: exception '{title}': {str(e)[:200]}")

    return state



def handle_medium(state: dict, content_bank: dict) -> dict:
    """Publish next blog article to Medium via Integration Token API."""
    token = os.environ.get("MEDIUM_TOKEN", "")
    if not token:
        log.error("MEDIUM_TOKEN missing")
        return state

    manifest = load_blog_manifest()
    if not manifest:
        log.error("Blog manifest is empty, nothing to publish")
        return state

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_medium") == today_str:
        log.info("Already published to Medium today (%s), skipping", today_str)
        return state

    published = state.get("medium_published", [])
    article = None
    for entry in manifest:
        if entry["slug"] not in published:
            article = entry
            break
    if article is None:
        log.info("All %d blog articles already published to Medium", len(manifest))
        return state

    slug = article["slug"]
    title = article["title"]
    summary = article["summary"]
    tags = article.get("tags", [])[:5]
    canonical_url = f"{SITE_URL}/blog/{slug}"

    # Resolve userId via GET /v1/me (cached in state)
    user_id = state.get("medium_user_id", "")
    if not user_id:
        try:
            me_resp = requests.get(
                "https://api.medium.com/v1/me",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=30,
            )
            user_id = me_resp.json().get("data", {}).get("id", "")
            if not user_id:
                log.error("Medium /v1/me failed: %s", me_resp.text[:300])
                return state
            state["medium_user_id"] = user_id
        except Exception as e:
            log.exception("Medium userId resolve failed")
            _send_telegram(f"❌ Medium: userId resolve failed: {str(e)[:200]}")
            return state

    content_md = (
        f"> *Originally published at [trendrider.net]({canonical_url})*\n\n"
        f"{summary}\n\n"
        f"## What You Will Learn\n\n"
        f"This article breaks down the complete strategy with real backtest data, "
        f"exact entry/exit rules, and Python code examples you can run today.\n\n"
        f"**[Read the full article on TrendRider →]({canonical_url})**\n\n"
        f"---\n\n"
        f"TrendRider is a free algorithmic crypto trading system with 67.9% "
        f"backtested win rate. The open-source Freqtrade strategy is on "
        f"[GitHub](https://github.com/darkvolg/trendrider-strategy) — star it if useful. "
        f"Live bot stats: [{SITE_URL}/live]({SITE_URL}/live)."
    )

    payload = {
        "title": title,
        "contentFormat": "markdown",
        "content": f"# {title}\n\n{content_md}",
        "tags": tags,
        "canonicalUrl": canonical_url,
        "publishStatus": "public",
    }

    log.info("Publishing to Medium: %s (slug=%s)", title, slug)
    try:
        resp = requests.post(
            f"https://api.medium.com/v1/users/{user_id}/posts",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Charset": "utf-8",
            },
            json=payload,
            timeout=60,
        )
        data = resp.json()
        if resp.status_code not in (200, 201) or "errors" in data:
            log.error("Medium publish failed (%s): %s", resp.status_code, data)
            _send_telegram(f"❌ Medium: ошибка '{title}'")
            return state
        post = data.get("data", {})
        post_url = post.get("url", "")
        log.info("Medium published: %s (id=%s)", post_url, post.get("id"))
        published.append(slug)
        state["medium_published"] = published
        state["last_medium"] = today_str
        _send_telegram(f"✅ Medium: опубликована '{title}'\n{post_url}")
    except Exception as e:
        log.exception("Medium publish exception")
        _send_telegram(f"❌ Medium: exception '{title}': {str(e)[:200]}")

    return state



def handle_linkedin(state: dict, content_bank: dict) -> dict:
    """Post next blog article to LinkedIn from blog manifest."""
    manifest = load_blog_manifest()
    if not manifest:
        log.error("Blog manifest is empty, nothing to publish")
        return state

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if state.get("last_linkedin") == today_str:
        log.info("Already posted to LinkedIn today (%s), skipping", today_str)
        return state

    published = state.get("linkedin_published", [])
    article = None
    for entry in manifest:
        if entry["slug"] not in published:
            article = entry
            break

    if article is None:
        log.info("All %d blog articles already posted to LinkedIn", len(manifest))
        return state

    slug = article["slug"]
    title = article["title"]
    summary = article["summary"]
    canonical_url = f"{SITE_URL}/blog/{slug}"

    author_urn = state.get("linkedin_author_urn", "")
    if not author_urn:
        log.info("Fetching LinkedIn profile to get author URN...")
        resp = _composio_mcp_call("LINKEDIN_GET_MY_INFO", {})
        data = _extract_composio_result(resp)
        if data and isinstance(data, dict):
            person_id = data.get("sub", data.get("id", ""))
            if person_id:
                author_urn = f"urn:li:person:{person_id}"
                state["linkedin_author_urn"] = author_urn
                log.info("LinkedIn author URN: %s", author_urn)
            else:
                log.error("Could not extract person ID from LinkedIn: %s", data)
                _send_telegram("\u274c LinkedIn: не удалось получить author URN")
                return state
        else:
            log.error("Failed to fetch LinkedIn profile info")
            _send_telegram("\u274c LinkedIn: не удалось получить профиль")
            return state

    commentary = (
        f"{title}\n\n"
        f"{summary}\n\n"
        f"Read more: {canonical_url}\n\n"
        f"#algotrading #crypto #trading #fintech"
    )[:3000]

    log.info("Posting to LinkedIn: '%s' (slug=%s)", title, slug)

    resp = _composio_mcp_call("LINKEDIN_CREATE_LINKED_IN_POST", {
        "author": author_urn,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "lifecycleState": "PUBLISHED",
    })
    data = _extract_composio_result(resp)

    if data and isinstance(data, dict) and (data.get("id") or data.get("activity") or data.get("x_restli_id")):
        post_id = data.get("id", data.get("activity", data.get("x_restli_id", "")))
        log.info("LinkedIn post published (id=%s)", post_id)
        published.append(slug)
        state["linkedin_published"] = published
        state["last_linkedin"] = today_str
        _send_telegram(f"\u2705 LinkedIn: опубликован пост '{title}'")
    else:
        log.error("LinkedIn post failed for '%s': %s", title, data)
        _send_telegram(f"\u274c LinkedIn: ошибка публикации '{title}'")

    return state


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Marketing Autopilot for TrendRider",
    )
    parser.add_argument(
        "--twitter", action="store_true",
        help="Post next tweet from content bank",
    )
    parser.add_argument(
        "--reddit", action="store_true",
        help="Post comment to Reddit from content bank",
    )
    parser.add_argument(
        "--remind", action="store_true",
        help="Send due Telegram reminders",
    )
    parser.add_argument(
        "--devto", action="store_true",
        help="Publish next article to Dev.to",
    )
    parser.add_argument(
        "--linkedin", action="store_true",
        help="Post next article to LinkedIn",
    )
    parser.add_argument(
        "--hashnode", action="store_true",
        help="Publish next article to Hashnode",
    )
    parser.add_argument(
        "--medium", action="store_true",
        help="Publish next article to Medium",
    )
    args = parser.parse_args()

    if not any([args.twitter, args.reddit, args.remind, args.devto, args.linkedin, args.hashnode, args.medium]):
        parser.print_help()
        sys.exit(1)

    log.info("=== Marketing Autopilot started ===")

    state = load_state()
    content_bank = load_content_bank()

    if args.twitter:
        log.info("--- Mode: Twitter ---")
        state = handle_twitter(state, content_bank)

    if args.reddit:
        log.info("--- Mode: Reddit ---")
        state = handle_reddit(state, content_bank)

    if args.remind:
        log.info("--- Mode: Remind ---")
        state = handle_remind(state, content_bank)

    if args.devto:
        log.info("--- Mode: Dev.to ---")
        state = handle_devto(state, content_bank)

    if args.linkedin:
        log.info("--- Mode: LinkedIn ---")
        state = handle_linkedin(state, content_bank)

    if args.hashnode:
        log.info("--- Mode: Hashnode ---")
        state = handle_hashnode(state, content_bank)

    if args.medium:
        log.info("--- Mode: Medium ---")
        state = handle_medium(state, content_bank)

    save_state(state)
    log.info("=== Marketing Autopilot finished ===")


if __name__ == "__main__":
    main()
