#!/usr/bin/env python3
"""IndexNow: push fresh URLs to Bing/Yandex for instant indexing.

Google ignores our sitemap (0/50 indexed as of 2026-04-14). IndexNow bypasses
that by pushing directly to Bing/Yandex (which DuckDuckGo and other engines
also consume). Free, unlimited, documented at indexnow.org.

Cron (after article_generator on Tue/Fri):
    30 9 * * 2,5 /usr/bin/python3 /opt/freqtrade/scripts/marketing/indexnow_submit.py --sitemap

Environment:
    TG_TOKEN / ADMIN_CHAT_ID - optional, Telegram ping on submit
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

SITE = "https://trendrider.net"
KEY = "fe7190ac1045473e94c3f51540ec1e02"
KEY_LOCATION = f"{SITE}/{KEY}.txt"
SITEMAP_URL = f"{SITE}/sitemap.xml"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/IndexNow"

TG_TOKEN = os.environ.get("TG_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

STATE_FILE = Path("/var/lib/indexnow_state.txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("indexnow")


def fetch_sitemap_urls() -> list[str]:
    """Parse sitemap.xml and return all URLs."""
    try:
        resp = requests.get(SITEMAP_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error("Failed to fetch sitemap: %s", e)
        return []

    try:
        root = ET.fromstring(resp.content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        return [el.text.strip() for el in root.findall(".//sm:url/sm:loc", ns) if el.text]
    except ET.ParseError as e:
        log.error("Failed to parse sitemap: %s", e)
        return []


def load_submitted() -> set[str]:
    if STATE_FILE.exists():
        try:
            return set(STATE_FILE.read_text().splitlines())
        except OSError:
            return set()
    return set()


def save_submitted(urls: set[str]) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text("\n".join(sorted(urls)))
    except OSError as e:
        log.error("Failed to persist state: %s", e)


def submit_urls(urls: list[str]) -> bool:
    """POST URL batch to IndexNow (max 10000 per request)."""
    if not urls:
        return True

    host = SITE.replace("https://", "").replace("http://", "")
    payload = {
        "host": host,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls[:10000],
    }
    try:
        resp = requests.post(
            INDEXNOW_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
    except requests.RequestException as e:
        log.error("IndexNow request failed: %s", e)
        return False

    if resp.status_code in (200, 202):
        log.info("IndexNow accepted %d URLs (HTTP %d)", len(urls), resp.status_code)
        return True

    log.error("IndexNow rejected: HTTP %d — %s", resp.status_code, resp.text[:200])
    return False


def notify_tg(msg: str) -> None:
    if not TG_TOKEN or not ADMIN_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": ADMIN_CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
    except requests.RequestException:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sitemap", action="store_true",
                        help="Submit all URLs from sitemap.xml")
    parser.add_argument("--url", action="append", default=[],
                        help="Submit specific URL(s), can repeat")
    parser.add_argument("--force", action="store_true",
                        help="Resubmit all URLs, even if seen before")
    args = parser.parse_args()

    if not args.sitemap and not args.url:
        parser.error("Provide --sitemap or --url")

    targets: list[str] = list(args.url)
    if args.sitemap:
        targets.extend(fetch_sitemap_urls())

    targets = sorted(set(u for u in targets if u.startswith("http")))
    if not targets:
        log.warning("No URLs to submit")
        return 1

    seen = set() if args.force else load_submitted()
    fresh = [u for u in targets if u not in seen]

    if not fresh:
        log.info("All %d URLs already submitted. Use --force to resubmit.", len(targets))
        return 0

    log.info("Submitting %d fresh URLs (of %d total)", len(fresh), len(targets))
    if submit_urls(fresh):
        save_submitted(seen | set(fresh))
        notify_tg(
            f"🔎 <b>IndexNow submitted</b>\n"
            f"Fresh URLs: {len(fresh)}\n"
            f"Total known: {len(seen | set(fresh))}"
        )
        return 0

    notify_tg(f"⚠️ IndexNow submission failed for {len(fresh)} URLs")
    return 1


if __name__ == "__main__":
    sys.exit(main())
