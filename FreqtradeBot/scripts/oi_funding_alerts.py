#!/usr/bin/env python3
"""
OI & Funding Rate Alert Monitor — sends alerts on spikes to Telegram.
Run via cron every 30 min: */30 * * * * /usr/bin/python3 /path/to/scripts/oi_funding_alerts.py
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))

PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "DOGE/USDT"]
OI_SPIKE_THRESHOLD = 5.0          # percent
FUNDING_ALERT_THRESHOLD = 0.0003  # 0.03%
FUNDING_EXTREME_THRESHOLD = 0.0005  # 0.05%
ALERT_COOLDOWN_HOURS = 4

COOLDOWN_FILE = os.path.join(FT_HOME, "user_data", "alert_cooldowns.json")

BYBIT_BASE = "https://api.bybit.com"


# ---------------------------------------------------------------------------
# Telegram helpers
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


def send_telegram(token: str, chat_id: str, text: str) -> None:
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
        if not resp.ok:
            print(f"[WARN] Telegram send failed: {resp.text}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Telegram error: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Cooldown logic
# ---------------------------------------------------------------------------
def load_cooldowns() -> dict[str, str]:
    """Load cooldown timestamps from JSON file."""
    if not os.path.exists(COOLDOWN_FILE):
        return {}
    try:
        with open(COOLDOWN_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_cooldowns(cooldowns: dict[str, str]) -> None:
    """Save cooldown timestamps to JSON file."""
    os.makedirs(os.path.dirname(COOLDOWN_FILE), exist_ok=True)
    with open(COOLDOWN_FILE, "w") as f:
        json.dump(cooldowns, f, indent=2)


def is_on_cooldown(cooldowns: dict[str, str], key: str) -> bool:
    """Check if an alert key is still within its cooldown window."""
    ts = cooldowns.get(key)
    if not ts:
        return False
    try:
        last = datetime.fromisoformat(ts)
        return datetime.now(timezone.utc) - last < timedelta(hours=ALERT_COOLDOWN_HOURS)
    except ValueError:
        return False


def set_cooldown(cooldowns: dict[str, str], key: str) -> None:
    """Mark an alert key as just fired."""
    cooldowns[key] = datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Bybit API helpers
# ---------------------------------------------------------------------------
def to_symbol(pair: str) -> str:
    """Convert 'BTC/USDT' to 'BTCUSDT'."""
    return pair.replace("/", "").replace(":USDT", "")


def fetch_open_interest(symbol: str) -> tuple[float | None, float | None]:
    """Fetch last two OI data points; return (current_oi, change_pct) or (None, None)."""
    url = f"{BYBIT_BASE}/v5/market/open-interest"
    params = {"category": "linear", "symbol": symbol, "intervalTime": "1h", "limit": 2}
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        rows = data.get("result", {}).get("list", [])
        if len(rows) < 2:
            return None, None
        oi_now = float(rows[0]["openInterest"])
        oi_prev = float(rows[1]["openInterest"])
        if oi_prev == 0:
            return oi_now, None
        change_pct = ((oi_now - oi_prev) / oi_prev) * 100
        return oi_now, change_pct
    except Exception as e:
        print(f"[WARN] OI fetch failed for {symbol}: {e}", file=sys.stderr)
        return None, None


def fetch_funding_rate(symbol: str) -> float | None:
    """Fetch latest funding rate for symbol."""
    url = f"{BYBIT_BASE}/v5/market/funding/history"
    params = {"category": "linear", "symbol": symbol, "limit": 1}
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        rows = data.get("result", {}).get("list", [])
        if not rows:
            return None
        return float(rows[0]["fundingRate"])
    except Exception as e:
        print(f"[WARN] Funding fetch failed for {symbol}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Alert formatting
# ---------------------------------------------------------------------------
def format_oi(oi: float) -> str:
    """Format OI value to human-readable string."""
    if oi >= 1e9:
        return f"${oi / 1e9:.1f}B"
    if oi >= 1e6:
        return f"${oi / 1e6:.1f}M"
    return f"${oi:,.0f}"


def build_oi_alert(pair: str, oi: float, change_pct: float) -> str:
    sign = "+" if change_pct > 0 else ""
    verb = "surged" if change_pct > 0 else "dropped"
    return (
        f"MARKET ALERT | OI SPIKE\n"
        f"========================\n"
        f"{pair} Open Interest {verb} {sign}{change_pct:.1f}% in 1h\n\n"
        f"Current OI: {format_oi(oi)}\n"
        f"This often precedes volatile moves.\n"
        f"Stay alert for breakout signals.\n"
        f"========================\n"
        f"TrendRider AI | @TrendRiderSignals"
    )


def build_funding_alert(pair: str, rate: float, extreme: bool) -> str:
    pct = rate * 100
    sign = "+" if rate > 0 else ""
    level = "EXTREME FUNDING" if extreme else "HIGH FUNDING"
    if rate > 0:
        side_desc = "longs paying shorts"
        bias = "overleveraged longs"
    else:
        side_desc = "shorts paying longs"
        bias = "overleveraged shorts"
    severity = "Extremely high" if extreme else "Elevated"
    return (
        f"MARKET ALERT | {level}\n"
        f"{'=' * 32}\n"
        f"{pair} Funding Rate: {sign}{pct:.4f}%\n"
        f"({severity} \u2014 {side_desc})\n\n"
        f"This indicates {bias}.\n"
        f"Watch for potential liquidation cascade.\n"
        f"{'=' * 32}\n"
        f"TrendRider AI | @TrendRiderSignals"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    token, chat_id = get_telegram_config()
    cooldowns = load_cooldowns()
    alerts_sent = 0

    for pair in PAIRS:
        symbol = to_symbol(pair)

        # --- Open Interest ---
        oi, oi_change = fetch_open_interest(symbol)
        if oi is not None and oi_change is not None and abs(oi_change) > OI_SPIKE_THRESHOLD:
            key = f"{symbol}_oi"
            if not is_on_cooldown(cooldowns, key):
                msg = build_oi_alert(pair, oi, oi_change)
                send_telegram(token, chat_id, msg)
                set_cooldown(cooldowns, key)
                alerts_sent += 1

        # --- Funding Rate ---
        rate = fetch_funding_rate(symbol)
        if rate is not None and abs(rate) >= FUNDING_ALERT_THRESHOLD:
            key = f"{symbol}_funding"
            if not is_on_cooldown(cooldowns, key):
                extreme = abs(rate) >= FUNDING_EXTREME_THRESHOLD
                msg = build_funding_alert(pair, rate, extreme)
                send_telegram(token, chat_id, msg)
                set_cooldown(cooldowns, key)
                alerts_sent += 1

    save_cooldowns(cooldowns)
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] "
          f"Checked {len(PAIRS)} pairs, sent {alerts_sent} alert(s)")


if __name__ == "__main__":
    main()
