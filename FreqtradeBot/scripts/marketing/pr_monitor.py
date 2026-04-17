#!/usr/bin/env python3
"""TrendRider PR monitor — sends Telegram alert on PR state changes.

Tracks 4 outreach PRs:
- botcrypto-io/awesome-crypto-trading-bots#95
- wangzhe3224/awesome-systematic-trading#84
- just-nilux/awesome-freqtrade#1
- suenot/awesome-crypto-trading#4

For each PR compares: state, merged, comments count, review comments count,
last commenter. If anything changed since last run, posts one combined
Telegram message to admin chat. State is persisted to pr_state.json.

Usage: python3 pr_monitor.py

Env vars required:
    TG_TOKEN       - Telegram bot token
    ADMIN_CHAT_ID  - Telegram chat id to notify

Run from cron once per day.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

__version__ = "1.3.0"

PRS = [
    ("botcrypto-io", "awesome-crypto-trading-bots", 95, "Awesome Crypto Trading Bots (2.4k⭐)"),
    ("wangzhe3224", "awesome-systematic-trading", 84, "Awesome Systematic Trading (3.8k⭐)"),
    ("just-nilux", "awesome-freqtrade", 1, "Awesome Freqtrade (первый PR в репо)"),
    ("suenot", "awesome-crypto-trading", 4, "Suenot / Crypto Trading"),
    ("thuquant", "awesome-quant", 35, "THU Awesome Quant (5.2k⭐)"),
    ("SpiralDevelopment", "Awesome-Crypto-Trading", 26, "Spiral Awesome Crypto Trading (190⭐ — added 2026-04-17)"),
    ("paperswithbacktest", "awesome-systematic-trading", 45, "Papers With Backtest (7.9k⭐ — added 2026-04-17)"),
    ("georgezouq", "awesome-ai-in-finance", 113, "Awesome AI in Finance (5.7k⭐ — самый крупный)"),
    ("freqtrade", "freqtrade-strategies", 334, "Freqtrade Strategies (5k⭐ — official strategy contribution)"),
]

STATE_FILE = Path(__file__).parent / "pr_state.json"
TG_TOKEN = os.environ.get("TG_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
USER_AGENT = "trendrider-pr-monitor/1.0"


def gh_get(url: str) -> dict | list | None:
    """Fetch JSON from GitHub public API, None on 404/5xx."""
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[WARN] HTTP {e.code} for {url}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[WARN] Fetch failed {url}: {e}", file=sys.stderr)
        return None


def fetch_pr_snapshot(owner: str, repo: str, num: int) -> dict | None:
    """Return lightweight PR snapshot dict with state fields we care about."""
    pr = gh_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}")
    if not pr:
        return None

    # Fetch issue comments (PR conversation) to see latest commenter
    comments = gh_get(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments?per_page=100"
    ) or []
    last_comment_author = ""
    last_comment_at = ""
    if comments:
        latest = comments[-1]
        last_comment_author = (latest.get("user") or {}).get("login", "")
        last_comment_at = latest.get("created_at", "")

    return {
        "state": pr.get("state", "unknown"),
        "merged": bool(pr.get("merged", False)),
        "merged_at": pr.get("merged_at"),
        "closed_at": pr.get("closed_at"),
        "comments": pr.get("comments", 0),
        "review_comments": pr.get("review_comments", 0),
        "last_comment_author": last_comment_author,
        "last_comment_at": last_comment_at,
        "html_url": pr.get("html_url", ""),
        "title": pr.get("title", ""),
    }


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def ru_plural(n: int, forms: tuple[str, str, str]) -> str:
    """Russian plural: forms = (1, 2-4, 5-20). Example: ('комментарий', 'комментария', 'комментариев')."""
    n = abs(n) % 100
    if 11 <= n <= 19:
        return forms[2]
    n %= 10
    if n == 1:
        return forms[0]
    if 2 <= n <= 4:
        return forms[1]
    return forms[2]


def diff_snapshot(old: dict | None, new: dict) -> list[str]:
    """Return list of human-readable changes in Russian, empty if nothing changed."""
    changes = []
    if old is None:
        return ["первый запуск — состояние зафиксировано"]
    if old.get("merged") != new.get("merged") and new.get("merged"):
        changes.append("🎉 <b>СМЕРДЖЕН!</b>")
    elif old.get("state") != new.get("state"):
        old_s = old.get("state", "?")
        new_s = new.get("state", "?")
        state_ru = {"open": "открыт", "closed": "закрыт"}
        changes.append(f"статус: {state_ru.get(old_s, old_s)} → {state_ru.get(new_s, new_s)}")
    if old.get("comments", 0) != new.get("comments", 0):
        delta = new["comments"] - old["comments"]
        if delta > 0:
            author = new.get("last_comment_author") or "?"
            word = ru_plural(delta, ("комментарий", "комментария", "комментариев"))
            changes.append(f"💬 +{delta} {word}, последний от @{author}")
    if old.get("review_comments", 0) != new.get("review_comments", 0):
        delta = new["review_comments"] - old["review_comments"]
        if delta > 0:
            word = ru_plural(delta, ("review-комментарий", "review-комментария", "review-комментариев"))
            changes.append(f"📝 +{delta} {word}")
    return changes


def tg_send(text: str) -> bool:
    if not TG_TOKEN or not ADMIN_CHAT_ID:
        print("[ERROR] TG_TOKEN / ADMIN_CHAT_ID missing", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = json.dumps(
        {
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[ERROR] Telegram send failed: {e}", file=sys.stderr)
        return False


def main() -> int:
    state = load_state()
    new_state = {}
    messages = []
    first_run = not state

    for owner, repo, num, label in PRS:
        key = f"{owner}/{repo}#{num}"
        print(f"[INFO] Проверяю {key} ({label})...")
        snap = fetch_pr_snapshot(owner, repo, num)
        if not snap:
            print(f"[WARN] Пропускаю {key}, fetch failed")
            # keep old state so we don't lose it
            if key in state:
                new_state[key] = state[key]
            continue

        new_state[key] = snap
        changes = diff_snapshot(state.get(key), snap)
        if changes and not first_run:
            emoji = "🎉" if snap.get("merged") else "📬"
            lines = [
                f"{emoji} <b>{label}</b>",
                f"<a href=\"{snap['html_url']}\">{key}</a>",
                *[f"  • {c}" for c in changes],
            ]
            messages.append("\n".join(lines))
        time.sleep(1)  # be nice to GitHub API

    save_state(new_state)

    if first_run:
        pr_word = ru_plural(len(PRS), ("PR", "PR", "PR"))
        header = "🟢 <b>Мониторинг PR запущен</b>\n"
        header += f"Отслеживаю <b>{len(PRS)}</b> {pr_word}. Сообщу при любых изменениях (новые комментарии, merge, close).\n\n"
        header += "Проверка каждый день в 10:05 МСК."
        tg_send(header)
        print("[INFO] Первый запуск — состояние зафиксировано.")
        return 0

    if not messages:
        print("[INFO] Изменений нет.")
        return 0

    changes_word = ru_plural(len(messages), ("изменение", "изменения", "изменений"))
    body = f"📊 <b>Обновления TrendRider PR</b>\n<i>найдено {len(messages)} {changes_word}</i>\n\n" + "\n\n".join(messages)
    if tg_send(body):
        print(f"[INFO] Отправлено {len(messages)} изменени(й) в Telegram.")
    else:
        print("[ERROR] Отправка в Telegram не удалась.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
