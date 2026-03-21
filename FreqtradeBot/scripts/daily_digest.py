#!/usr/bin/env python3
"""
Daily Morning Digest — sends market overview to Telegram.
Run via cron: 0 8 * * * /usr/bin/python3 /path/to/scripts/daily_digest.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import ccxt
import numpy as np
import requests
import talib

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
TIMEFRAME = "1h"
CANDLE_LIMIT = 210  # enough for EMA200 + warm-up
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))


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
# Market helpers
# ---------------------------------------------------------------------------

def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str) -> np.ndarray | None:
    """Fetch OHLCV candles; return numpy array of closes or None."""
    try:
        candles = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=CANDLE_LIMIT)
        if not candles or len(candles) < 50:
            return None
        return np.array(candles, dtype=float)
    except Exception as e:
        print(f"[WARN] Failed to fetch {symbol}: {e}", file=sys.stderr)
        return None


def analyse_pair(exchange: ccxt.Exchange, symbol: str) -> dict:
    """Return analysis dict for a single pair."""
    data = fetch_ohlcv(exchange, symbol)
    if data is None:
        return {"symbol": symbol, "error": True}

    closes = data[:, 4]  # close prices
    current_price = closes[-1]

    # 24h change (24 hourly candles back)
    idx_24h = min(24, len(closes) - 1)
    price_24h_ago = closes[-idx_24h - 1]
    change_pct = ((current_price - price_24h_ago) / price_24h_ago) * 100

    # RSI(14)
    rsi_arr = talib.RSI(closes, timeperiod=14)
    rsi = rsi_arr[-1]

    # EMA50 vs EMA200 trend
    ema50 = talib.EMA(closes, timeperiod=50)[-1]
    ema200 = talib.EMA(closes, timeperiod=200)[-1]

    if np.isnan(ema200):
        trend = "N/A"
    elif ema50 > ema200:
        trend = "Uptrend"
    else:
        trend = "Downtrend"

    # Status from RSI
    if rsi >= 70:
        status = "Overbought"
    elif rsi <= 30:
        status = "Oversold"
    else:
        status = "Neutral"

    return {
        "symbol": symbol,
        "error": False,
        "price": current_price,
        "change_pct": change_pct,
        "rsi": rsi,
        "trend": trend,
        "status": status,
        "ema50": ema50,
        "ema200": ema200,
    }


def format_price(price: float) -> str:
    """Format price with commas; drop decimals for big numbers."""
    if price >= 100:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:,.4f}"


def build_message(results: list[dict]) -> str:
    """Build the Telegram message string."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%-d %b %Y")

    lines = [
        f"*MORNING BRIEF* | {date_str}",
        "================================",
        "",
    ]

    btc_result = None
    for r in results:
        sym = r["symbol"]
        if r.get("error"):
            lines.append(f"*{sym}:* _data unavailable_")
            lines.append("")
            continue

        sign = "+" if r["change_pct"] >= 0 else ""
        price_str = format_price(r["price"])
        lines.append(
            f"*{sym}:* `{price_str}` ({sign}{r['change_pct']:.1f}%)"
        )
        lines.append(
            f"  Trend: {r['trend']} | RSI: {r['rsi']:.0f} | Status: {r['status']}"
        )
        lines.append("")

        if "BTC" in sym:
            btc_result = r

    # Market summary
    btc_dom = "flat"
    if btc_result and not btc_result.get("error"):
        if btc_result["change_pct"] > 1:
            btc_dom = "up"
        elif btc_result["change_pct"] < -1:
            btc_dom = "down"

    lines.append("*Market Summary:*")
    lines.append(f"  BTC Dominance trend: {btc_dom}")
    lines.append("  Active signals: waiting for entries")
    lines.append("================================")
    lines.append("_TrendRider Algo | @TrendRiderSignals_")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=15)
    if not resp.ok:
        print(f"[ERROR] Telegram API: {resp.status_code} {resp.text}", file=sys.stderr)
    else:
        print("[OK] Digest sent to Telegram.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    token, chat_id = get_telegram_config()

    try:
        exchange = ccxt.bybit({"enableRateLimit": True})
        exchange.load_markets()
    except Exception as e:
        send_telegram(token, chat_id, f"*MORNING BRIEF*\n\n_Exchange unavailable: {e}_")
        sys.exit(1)

    results = [analyse_pair(exchange, pair) for pair in PAIRS]
    message = build_message(results)
    send_telegram(token, chat_id, message)


if __name__ == "__main__":
    main()
