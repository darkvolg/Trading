#!/usr/bin/env python3
"""
Daily Morning Digest — sends market overview to Telegram.
Run via cron: 0 8 * * * /usr/bin/python3 /path/to/scripts/daily_digest.py
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

import requests

try:
    import ccxt
    import numpy as np
    import talib
except ImportError as e:
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
    _notify_error(f"daily_digest.py: Import error: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
TIMEFRAME = "1h"
CANDLE_LIMIT = 210  # enough for EMA200 + warm-up
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))
DB_PATH = os.getenv("FT_DB_PATH", os.path.join(FT_HOME, "tradesv3.dryrun.sqlite"))
MAX_POSITIONS = 4


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

def pair_to_bybit(pair: str) -> str:
    """Convert pair like 'BTC/USDT' to Bybit symbol 'BTCUSDT'."""
    return pair.replace("/", "").replace(":USDT", "")


def fetch_fng() -> dict:
    """Fetch Fear & Greed Index."""
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        data = resp.json()["data"][0]
        return {"value": int(data["value"]), "label": data["value_classification"]}
    except Exception:
        return {"value": 0, "label": "N/A"}


def fetch_funding_rate(symbol: str) -> float | None:
    """Fetch latest funding rate from Bybit."""
    try:
        url = "https://api.bybit.com/v5/market/funding/history"
        params = {"category": "linear", "symbol": symbol, "limit": 1}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        rate = float(data["result"]["list"][0]["fundingRate"])
        return rate
    except Exception:
        return None


def fetch_oi_change(symbol: str) -> float | None:
    """Fetch 24h OI change % from Bybit."""
    try:
        url = "https://api.bybit.com/v5/market/open-interest"
        params = {"category": "linear", "symbol": symbol, "intervalTime": "1h", "limit": 25}
        resp = requests.get(url, params=params, timeout=10)
        oi_list = resp.json()["result"]["list"]
        if len(oi_list) < 2:
            return None
        current_oi = float(oi_list[0]["openInterest"])
        old_oi = float(oi_list[-1]["openInterest"])
        if old_oi == 0:
            return None
        return ((current_oi - old_oi) / old_oi) * 100
    except Exception:
        return None


def get_open_positions() -> int:
    """Count open positions from SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("SELECT count(*) FROM trades WHERE is_open = 1")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def classify_funding(rate: float | None) -> str:
    """Classify funding rate as bullish/bearish/neutral."""
    if rate is None:
        return "N/A"
    if rate < -0.0001:  # < -0.01%
        return "bullish"
    elif rate > 0.0003:  # > 0.03%
        return "bearish"
    else:
        return "neutral"


def portfolio_heat(count: int) -> str:
    """Return heat label based on open position count."""
    if count == 0:
        return "COLD"
    elif count <= 2:
        return "MODERATE"
    else:
        return "HOT"


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
    highs = data[:, 2]
    lows = data[:, 3]
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

    # ADX(14)
    adx_arr = talib.ADX(highs, lows, closes, timeperiod=14)
    adx = adx_arr[-1] if not np.isnan(adx_arr[-1]) else None

    # Funding rate
    bybit_sym = pair_to_bybit(symbol)
    funding = fetch_funding_rate(bybit_sym)

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
        "adx": adx,
        "funding": funding,
    }


def format_price(price: float) -> str:
    """Format price with commas; drop decimals for big numbers."""
    if price >= 100:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:,.4f}"


def build_message(results: list[dict], fng: dict, open_pos: int,
                  oi_changes: dict[str, float | None]) -> str:
    """Build the Telegram message string."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%-d %b %Y")

    lines = [
        f"*MORNING BRIEF* | {date_str}",
        "================================",
        "",
    ]

    # --- MARKET PULSE ---
    lines.append("*MARKET PULSE*")
    lines.append(f"Fear & Greed: {fng['value']} ({fng['label']})")

    # BTC Regime (ADX)
    btc_result = None
    for r in results:
        if "BTC" in r["symbol"] and not r.get("error"):
            btc_result = r
            break

    if btc_result and btc_result.get("adx") is not None:
        adx_val = btc_result["adx"]
        regime = "Trending" if adx_val >= 25 else "Ranging"
        lines.append(f"BTC Regime: {regime} (ADX {adx_val:.0f})")
    else:
        lines.append("BTC Regime: N/A")

    heat = portfolio_heat(open_pos)
    lines.append(f"Portfolio: {open_pos}/{MAX_POSITIONS} positions ({heat})")
    lines.append("")

    # --- Per-pair data ---
    for r in results:
        sym = r["symbol"]
        if r.get("error"):
            lines.append(f"*{sym}:* _data unavailable_")
            lines.append("")
            continue

        sign = "+" if r["change_pct"] >= 0 else ""
        price_str = format_price(r["price"])

        # Funding display
        if r["funding"] is not None:
            fund_pct = r["funding"] * 100  # convert to percentage
            fund_sign = "+" if fund_pct >= 0 else ""
            fund_str = f"{fund_sign}{fund_pct:.3f}%"
        else:
            fund_str = "N/A"

        lines.append(
            f"*{sym}:* `{price_str}` ({sign}{r['change_pct']:.1f}%)"
        )
        lines.append(
            f"  Trend: {r['trend']} | RSI: {r['rsi']:.0f} | Funding: {fund_str}"
        )
        lines.append("")

    # --- OI Changes ---
    lines.append("*OI CHANGES (24h)*")
    oi_parts = []
    for r in results:
        sym_short = r["symbol"].split("/")[0]
        bybit_sym = pair_to_bybit(r["symbol"])
        oi_val = oi_changes.get(bybit_sym)
        if oi_val is not None:
            oi_sign = "+" if oi_val >= 0 else ""
            oi_parts.append(f"{sym_short}: {oi_sign}{oi_val:.1f}%")
        else:
            oi_parts.append(f"{sym_short}: N/A")
    lines.append(" | ".join(oi_parts))
    lines.append("")

    # Market summary
    btc_dom = "flat"
    if btc_result and not btc_result.get("error"):
        if btc_result["change_pct"] > 1:
            btc_dom = "up"
        elif btc_result["change_pct"] < -1:
            btc_dom = "down"

    lines.append("*Market Summary:*")
    lines.append(f"  BTC trend: {btc_dom} | Active signals: waiting")
    lines.append("================================")
    lines.append("_TrendRider AI | @TrendRiderSignals_")

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

    # Fetch global data
    fng = fetch_fng()
    open_pos = get_open_positions()

    # Analyse each pair
    results = [analyse_pair(exchange, pair) for pair in PAIRS]

    # Fetch OI changes for all pairs
    oi_changes: dict[str, float | None] = {}
    for pair in PAIRS:
        bybit_sym = pair_to_bybit(pair)
        oi_changes[bybit_sym] = fetch_oi_change(bybit_sym)

    message = build_message(results, fng, open_pos, oi_changes)
    send_telegram(token, chat_id, message)


if __name__ == "__main__":
    main()
