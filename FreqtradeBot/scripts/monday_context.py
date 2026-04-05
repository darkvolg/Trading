#!/usr/bin/env python3
"""
Monday Market Context — sends weekly market overview to Telegram.
Run via cron: 0 8 * * 1 /usr/bin/python3 /path/to/scripts/monday_context.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests

try:
    import ccxt
    import numpy as np
    import talib
except ImportError as e:
    # Minimal fallback to notify about missing dependency
    import requests as _req
    def _notify_error(msg):
        try:
            token = os.getenv("TG_TOKEN", "")
            chat_id = os.getenv("TG_CHAT_ID", "")
            if token and chat_id:
                _req.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": msg}, timeout=10)
        except Exception:
            pass
    _notify_error(f"monday_context.py: Import error: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))
PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
TIMEFRAME = "1h"
CANDLE_LIMIT = 210  # enough for EMA200 + warm-up


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
    """Fetch OHLCV candles; return numpy array or None."""
    try:
        candles = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=CANDLE_LIMIT)
        if not candles or len(candles) < 50:
            return None
        return np.array(candles, dtype=float)
    except Exception as e:
        print(f"[WARN] Failed to fetch {symbol}: {e}", file=sys.stderr)
        return None


def fetch_fear_greed() -> tuple[int, str]:
    """Fetch Fear & Greed Index. Returns (value, label) or (-1, 'N/A')."""
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        data = resp.json()["data"][0]
        return int(data["value"]), data["value_classification"]
    except Exception as e:
        print(f"[WARN] FNG fetch failed: {e}", file=sys.stderr)
        return -1, "N/A"


def analyse_pair(exchange: ccxt.Exchange, symbol: str) -> dict:
    """Return analysis dict for a single pair."""
    data = fetch_ohlcv(exchange, symbol)
    if data is None:
        return {"symbol": symbol, "error": True}

    closes = data[:, 4]
    highs = data[:, 2]
    lows = data[:, 3]
    current_price = closes[-1]

    # 7-day change (168 hourly candles)
    if len(closes) < 170:
        change_7d = None
    else:
        idx_7d = min(168, len(closes) - 1)
        price_7d_ago = closes[-idx_7d - 1]
        change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100

    # RSI(14)
    rsi = talib.RSI(closes, timeperiod=14)[-1]

    # EMA50 / EMA200
    ema50 = talib.EMA(closes, timeperiod=50)[-1]
    ema200 = talib.EMA(closes, timeperiod=200)[-1]

    if np.isnan(ema200):
        trend = "N/A"
    elif ema50 > ema200:
        trend = "Uptrend"
    else:
        trend = "Downtrend"

    # ADX(14)
    adx = talib.ADX(highs, lows, closes, timeperiod=14)[-1]

    return {
        "symbol": symbol,
        "error": False,
        "price": current_price,
        "change_7d": change_7d,
        "rsi": rsi,
        "trend": trend,
        "ema50": ema50,
        "ema200": ema200,
        "adx": adx,
    }


def format_price(price: float) -> str:
    """Format price with commas; drop decimals for big numbers."""
    if price >= 100:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:,.4f}"


def build_message(results: list[dict], fng_value: int, fng_label: str) -> str:
    """Build the weekly context Telegram message."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%-d %b %Y")

    btc = next((r for r in results if "BTC" in r["symbol"]), None)

    # --- Macro overview ---
    if fng_value >= 0:
        fng_str = f"{fng_value} ({fng_label})"
    else:
        fng_str = "N/A"

    btc_trend_str = btc["trend"] if btc and not btc.get("error") else "N/A"
    ema_note = ""
    if btc and not btc.get("error") and btc_trend_str != "N/A":
        ema_note = " (EMA50 > EMA200)" if btc_trend_str == "Uptrend" else " (EMA50 < EMA200)"

    adx_val = btc["adx"] if btc and not btc.get("error") else float("nan")
    if np.isnan(adx_val):
        regime_str = "N/A"
    elif adx_val >= 25:
        regime_str = f"Trending (ADX {adx_val:.0f})"
    else:
        regime_str = f"Ranging (ADX {adx_val:.0f})"

    lines = [
        f"WEEKLY MARKET CONTEXT | {date_str}",
        "=====================================",
        "",
        "MACRO OVERVIEW",
        f"Fear & Greed: {fng_str}",
        f"BTC Trend: {btc_trend_str}{ema_note}",
        f"Market Regime: {regime_str}",
        "",
        "WATCHLIST",
    ]

    # --- Watchlist ---
    for r in results:
        sym = r["symbol"]
        if r.get("error"):
            lines.append(f"{sym}: data unavailable")
            continue
        price_str = format_price(r["price"])
        if r["change_7d"] is None:
            change_str = "N/A"
        else:
            sign = "+" if r["change_7d"] >= 0 else ""
            change_str = f"{sign}{r['change_7d']:.1f}%"
        lines.append(
            f"{sym}: {price_str} ({change_str} 7d) | RSI {r['rsi']:.0f}"
        )

    # --- What we're watching ---
    observations = _build_observations(btc, fng_value, fng_label)
    lines.append("")
    lines.append("WHAT WE'RE WATCHING")
    for obs in observations:
        lines.append(f"- {obs}")

    lines.append("")
    lines.append("=====================================")
    lines.append("TrendRider AI | @TrendRiderSignals")

    return "\n".join(lines)


def _build_observations(btc: dict | None, fng_value: int, fng_label: str) -> list[str]:
    """Generate 2-4 contextual observations."""
    obs: list[str] = []

    if btc and not btc.get("error"):
        # EMA relationship
        if btc["trend"] == "Uptrend":
            obs.append("BTC holding above EMA200 — bullish")
        elif btc["trend"] == "Downtrend":
            obs.append("BTC below EMA200 — caution warranted")

        # RSI context
        rsi = btc["rsi"]
        if rsi >= 70:
            obs.append("RSI overbought — watch for pullback")
        elif rsi <= 30:
            obs.append("RSI oversold — potential bounce zone")
        elif 40 <= rsi <= 60:
            obs.append("RSI neutral, room for movement")
        elif rsi > 60:
            obs.append("RSI leaning bullish, momentum building")
        else:
            obs.append("RSI leaning bearish, weak momentum")

        # ADX context
        if not np.isnan(btc["adx"]):
            if btc["adx"] >= 25:
                obs.append(f"ADX {btc['adx']:.0f} — strong trend, ride the wave")
            else:
                obs.append(f"ADX {btc['adx']:.0f} — choppy market, tighter stops advised")

    # FNG context
    if fng_value >= 0:
        if fng_value <= 25:
            obs.append("Extreme Fear — contrarian opportunity?")
        elif fng_value <= 45:
            obs.append("FNG in Fear territory — potential opportunity")
        elif fng_value >= 75:
            obs.append("Extreme Greed — distribution risk")
        elif fng_value >= 55:
            obs.append("FNG in Greed — stay selective")

    return obs or ["Market conditions mixed — stay disciplined"]


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
        print("[OK] Monday context sent to Telegram.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    token, chat_id = get_telegram_config()

    try:
        exchange = ccxt.bybit({"enableRateLimit": True})
        exchange.load_markets()
    except Exception as e:
        send_telegram(token, chat_id, f"WEEKLY MARKET CONTEXT\n\n_Exchange unavailable: {e}_")
        sys.exit(1)

    results = [analyse_pair(exchange, pair) for pair in PAIRS]
    fng_value, fng_label = fetch_fear_greed()
    message = build_message(results, fng_value, fng_label)
    send_telegram(token, chat_id, message)


if __name__ == "__main__":
    main()
