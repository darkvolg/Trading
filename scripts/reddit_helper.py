"""
Reddit Helper — browse, search, and comment on Reddit via Composio MCP API.

Usage:
    python reddit_helper.py browse [subreddit] [sort]     # Browse posts (hot/new/top)
    python reddit_helper.py comment <post_id> "text"      # Post a comment
    python reddit_helper.py search "query" [subreddit]    # Search posts
    python reddit_helper.py reply <comment_id> "text"     # Reply to a comment

Examples:
    python reddit_helper.py browse algotrading hot
    python reddit_helper.py comment 1s37rar "Great insight!"
    python reddit_helper.py search "freqtrade strategy" algotrading
    python reddit_helper.py reply t1_abc123 "I agree!"
"""

import sys
import json
import time
import re
import urllib.request
import urllib.error
import os

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "ck_pXu5W1IzK03__DGxggUc")
MCP_URL = "https://connect.composio.dev/mcp"


def mcp_call(tool_slug: str, arguments: dict) -> dict:
    """Execute a tool via Composio MCP endpoint."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {
            "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
            "arguments": {
                "tools": [{"tool_slug": tool_slug, "arguments": arguments}]
            },
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-CONSUMER-API-KEY": COMPOSIO_API_KEY,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(MCP_URL, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()

        # MCP returns SSE format — extract last JSON data line
        lines = raw.strip().split("\n")
        for line in reversed(lines):
            if line.startswith("data: "):
                return json.loads(line[6:])
            # Try parsing as plain JSON
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

        # Fallback: try parsing whole response
        return json.loads(raw)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {error_body[:500]}")
        sys.exit(1)


def extract_result(response: dict) -> dict:
    """Extract the actual result data from MCP response."""
    # Navigate: result -> content -> text (JSON string) -> parse
    result = response.get("result", {})
    content = result.get("content", [])
    for item in content:
        if item.get("type") == "text":
            try:
                return json.loads(item["text"])
            except (json.JSONDecodeError, KeyError):
                return item
    return result


def browse_posts(subreddit: str = "algotrading", sort: str = "hot", limit: int = 15):
    """Browse posts from a subreddit."""
    resp = mcp_call("REDDIT_FETCH_SUBREDDIT_POSTS", {
        "subreddit": subreddit,
        "sort": sort,
        "limit": limit,
    })
    data = extract_result(resp)

    # Try to find posts in various response formats
    posts = []
    if isinstance(data, dict):
        posts = data.get("posts", data.get("data", {}).get("children", []))
    elif isinstance(data, list):
        posts = data

    print(f"\n{'='*70}")
    print(f"  r/{subreddit} - {sort.upper()} ({len(posts)} posts)")
    print(f"{'='*70}\n")

    for i, post in enumerate(posts, 1):
        # Handle both flat and nested (children[].data) formats
        p = post.get("data", post) if isinstance(post, dict) else post
        title = p.get("title", "?")
        author = p.get("author", "?")
        score = p.get("score", p.get("ups", "?"))
        comments = p.get("num_comments", "?")
        post_id = p.get("id", p.get("name", "?"))
        selftext = p.get("selftext", p.get("body", ""))
        flair = p.get("link_flair_text", "")

        flair_str = f" [{flair}]" if flair else ""
        print(f"  {i:2d}. {title}{flair_str}")
        print(f"      u/{author} | {score} pts | {comments} comments | id: {post_id}")
        if selftext:
            preview = selftext[:150].replace("\n", " ").strip()
            print(f"      > {preview}...")
        print()


def post_comment(thing_id: str, text: str, retry: bool = True):
    """Post a comment. Auto-adds t3_ prefix for post IDs."""
    if not thing_id.startswith("t3_") and not thing_id.startswith("t1_"):
        thing_id = f"t3_{thing_id}"

    print(f"Posting comment to {thing_id}...")
    print(f"Text preview: {text[:100]}...")
    print()

    resp = mcp_call("REDDIT_POST_REDDIT_COMMENT", {
        "thing_id": thing_id,
        "text": text,
    })
    data = extract_result(resp)

    # Check for rate limit
    data_str = json.dumps(data)
    if "rate limit" in data_str.lower() or "take a break" in data_str.lower():
        # Extract wait time
        match = re.search(r"(\d+)\s*minute", data_str)
        wait_minutes = int(match.group(1)) if match else 10
        wait_seconds = (wait_minutes + 1) * 60

        if retry:
            print(f"Rate limited! Waiting {wait_minutes + 1} minutes...")
            time.sleep(wait_seconds)
            print("Retrying...")
            return post_comment(thing_id, text, retry=False)
        else:
            print(f"Still rate limited. Try again in {wait_minutes} minutes.")
            return None

    # Success — try to extract permalink
    try:
        things = data.get("data", {}).get("json", {}).get("data", {}).get("things", [])
        if things:
            comment_data = things[0].get("data", {})
            permalink = comment_data.get("permalink", "")
            fullname = comment_data.get("name", "")
            url = f"https://www.reddit.com{permalink}" if permalink else ""
            print(f"Comment posted!")
            print(f"  ID: {fullname}")
            if url:
                print(f"  URL: {url}")
            return comment_data
    except (KeyError, IndexError, TypeError):
        pass

    print("Response:")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    return data


def search_posts(query: str, subreddit: str = "", limit: int = 10):
    """Search Reddit posts."""
    args = {"search_query": query, "limit": limit, "sort": "new"}
    if subreddit:
        args["subreddit"] = subreddit

    resp = mcp_call("REDDIT_SEARCH_ACROSS_SUBREDDITS", args)
    data = extract_result(resp)

    posts = []
    if isinstance(data, dict):
        posts = data.get("posts", data.get("data", {}).get("children", []))

    print(f"\n  Search: '{query}'" + (f" in r/{subreddit}" if subreddit else ""))
    print(f"  Found {len(posts)} results\n")

    for i, post in enumerate(posts, 1):
        p = post.get("data", post) if isinstance(post, dict) else post
        title = p.get("title", "?")
        sub = p.get("subreddit", "?")
        score = p.get("score", "?")
        post_id = p.get("id", "?")
        print(f"  {i}. [{sub}] {title}")
        print(f"     {score} pts | id: {post_id}")
        print()


def batch_comment(comments: list[dict], delay_minutes: int = 10):
    """Post multiple comments with delay between them.

    comments: list of {"thing_id": "...", "text": "..."}
    """
    print(f"Batch posting {len(comments)} comments with {delay_minutes}min delay\n")

    for i, c in enumerate(comments, 1):
        print(f"--- Comment {i}/{len(comments)} ---")
        post_comment(c["thing_id"], c["text"])

        if i < len(comments):
            wait = delay_minutes * 60
            print(f"\nWaiting {delay_minutes} minutes before next comment...")
            for remaining in range(wait, 0, -60):
                print(f"  {remaining // 60} min remaining...", end="\r")
                time.sleep(min(60, remaining))
            print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "browse":
        subreddit = sys.argv[2] if len(sys.argv) > 2 else "algotrading"
        sort = sys.argv[3] if len(sys.argv) > 3 else "hot"
        browse_posts(subreddit, sort)

    elif cmd == "comment":
        if len(sys.argv) < 4:
            print("Usage: reddit_helper.py comment <post_id> \"text\"")
            return
        post_comment(sys.argv[2], sys.argv[3])

    elif cmd == "reply":
        if len(sys.argv) < 4:
            print("Usage: reddit_helper.py reply <comment_id> \"text\"")
            return
        cid = sys.argv[2]
        if not cid.startswith("t1_"):
            cid = f"t1_{cid}"
        post_comment(cid, sys.argv[3])

    elif cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "freqtrade"
        subreddit = sys.argv[3] if len(sys.argv) > 3 else ""
        search_posts(query, subreddit)

    elif cmd == "batch":
        # Read comments from JSON file
        if len(sys.argv) < 3:
            print("Usage: reddit_helper.py batch <comments.json> [delay_minutes]")
            return
        with open(sys.argv[2]) as f:
            comments = json.load(f)
        delay = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        batch_comment(comments, delay)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
