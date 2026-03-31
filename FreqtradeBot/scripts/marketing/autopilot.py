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
                return json.loads(item["text"])
            except (json.JSONDecodeError, KeyError):
                return item
    return result


def _fetch_recent_posts(subreddit: str, sort: str = "new", limit: int = 20) -> list:
    """Fetch recent posts from a subreddit via Composio."""
    resp = _composio_mcp_call("REDDIT_FETCH_SUBREDDIT_POSTS", {
        "subreddit": subreddit,
        "sort": sort,
        "limit": limit,
    })
    data = _extract_composio_result(resp)
    if not data:
        return []

    posts = []
    if isinstance(data, dict):
        posts = data.get("posts", data.get("data", {}).get("children", []))
    elif isinstance(data, list):
        posts = data

    return posts


def _pick_matching_post(posts: list, keywords: list[str]) -> dict | None:
    """Find the first post whose title or body matches any keyword."""
    for post in posts:
        p = post.get("data", post) if isinstance(post, dict) else post
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

    matched = _pick_matching_post(posts, REDDIT_KEYWORDS)
    if not matched:
        log.warning(
            "No posts matched keywords in r/%s (%d posts checked). "
            "Falling back to first post.",
            REDDIT_SUBREDDIT, len(posts),
        )
        # Use the first post with more than 0 comments as fallback
        for post in posts:
            p = post.get("data", post) if isinstance(post, dict) else post
            if p.get("num_comments", 0) >= 0:
                matched = p
                break

    if not matched:
        log.error("No suitable post found at all")
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


def handle_twitter(state: dict, content_bank: dict) -> dict:
    """Post next tweet from content bank."""
    tweets = content_bank.get("twitter_posts", [])
    if not tweets:
        log.error("No twitter_posts in content bank")
        return state

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last = state.get("last_twitter", "")
    # Allow 2 tweets per day (morning + evening) by tracking count
    today_count = state.get("twitter_today_count", 0)
    if last == today_str and today_count >= 2:
        log.info("Already posted 2 tweets today (%s), skipping", today_str)
        return state
    if last != today_str:
        today_count = 0

    idx = state.get("twitter_index", 0) % len(tweets)
    tweet_obj = tweets[idx]
    tweet_text = tweet_obj["text"] if isinstance(tweet_obj, dict) else str(tweet_obj)

    log.info("Posting tweet #%d (of %d): %s", idx + 1, len(tweets), tweet_text[:80])

    if twitter_post(tweet_text):
        state["twitter_index"] = (idx + 1) % len(tweets)
        state["last_twitter"] = today_str
        state["twitter_today_count"] = today_count + 1
        log.info("Twitter index advanced to %d", state["twitter_index"])
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
    args = parser.parse_args()

    if not any([args.twitter, args.reddit, args.remind]):
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

    save_state(state)
    log.info("=== Marketing Autopilot finished ===")


if __name__ == "__main__":
    main()
