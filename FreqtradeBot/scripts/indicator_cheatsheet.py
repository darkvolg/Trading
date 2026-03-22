#!/usr/bin/env python3
"""
Send an Indicator Cheat Sheet post to the TrendRider Telegram channel.
One-time script — run once, then delete or archive.
"""

import json
import os
import sys

import requests

FT_HOME = os.environ.get(
    "FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))


def get_telegram_config() -> tuple:
    """Return (token, chat_id) from env vars or Freqtrade config.json."""
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if token and chat_id:
        return token, chat_id
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        tg = cfg.get("telegram", {})
        return tg["token"], str(tg["chat_id"])
    except (FileNotFoundError, KeyError) as exc:
        sys.exit(f"Cannot read Telegram credentials: {exc}")


CHEATSHEET_TEXT = """
📊 *Indicator Cheat Sheet*

A quick reference for every indicator used in TrendRider signals\\.
Bookmark this — you'll come back to it\\.

━━━━━━━━━━━━━━━━━━━━━━

*1\\. RSI \\(Relative Strength Index\\)*

Measures momentum on a 0–100 scale\\.

• Below 30 \\= oversold \\(potential bounce\\)
• Above 70 \\= overbought \\(potential pullback\\)
• TrendRider sweet spot: *35–60*

_We enter longs when RSI is not yet overbought — room to run\\._

━━━━━━━━━━━━━━━━━━━━━━

*2\\. ADX \\(Average Directional Index\\)*

Trend strength on a 0–100 scale\\.

• Below 20 \\= no trend \\(choppy market, stay out\\)
• 20–30 \\= moderate trend
• Above 30 \\= strong trend

_We only trade when ADX \\> 20\\. No trend \\= no trade\\._

━━━━━━━━━━━━━━━━━━━━━━

*3\\. MACD \\(Moving Average Convergence Divergence\\)*

Momentum \\+ trend direction in one indicator\\.

• Histogram positive \\+ rising \\= bullish momentum
• Histogram negative \\+ falling \\= bearish momentum
• Key signal: histogram crossing zero line

_We look for MACD histogram flipping from negative to positive for long entries\\._

━━━━━━━━━━━━━━━━━━━━━━

*4\\. EMA \\(Exponential Moving Average\\)*

• *EMA16* — fast line for entries
• *EMA50* — support for deep pullbacks
• *EMA200* — the big trend filter

Price above EMA200 \\= bullish bias\\.
Price below EMA200 \\= bearish bias\\.

_TrendRider uses EMA crossovers to time entries and exits\\._

━━━━━━━━━━━━━━━━━━━━━━

*5\\. Bollinger Bands*

Volatility envelope around price\\.

• Price at lower band in uptrend \\= buy zone
• Price at upper band in downtrend \\= sell zone
• Band width shows current volatility

_Narrow bands \\= compression \\= breakout incoming\\._

━━━━━━━━━━━━━━━━━━━━━━

*6\\. Fear \\& Greed Index*

Crypto market sentiment on a 0–100 scale\\.

• Extreme Fear \\(<25\\) \\= contrarian buy opportunity
• Extreme Greed \\(\\>75\\) \\= caution, potential top
• Neutral zone: 40–60

_We use this as a macro filter — best entries come during fear\\._

━━━━━━━━━━━━━━━━━━━━━━

*7\\. Funding Rate \\& Open Interest*

Perpetual futures data from exchanges\\.

• High funding \\= crowded long \\(risk of squeeze\\)
• Negative funding \\= crowded short \\(risk of short squeeze\\)
• OI spikes \\= incoming volatility

_Extreme funding \\+ rising OI \\= be cautious with direction\\._

━━━━━━━━━━━━━━━━━━━━━━

_These indicators work together — no single one is a magic bullet\\. TrendRider's confidence score weighs ALL of them\\._

*Channel:* @TrendRiderSignals
""".strip()


def send_message(token: str, chat_id: str, text: str) -> int:
    """Send a Markdown message and return the message_id."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    data = resp.json()
    if not data.get("ok"):
        sys.exit(f"sendMessage failed: {data}")
    msg_id = data["result"]["message_id"]
    print(f"Message sent (id={msg_id})")
    return msg_id


def main() -> None:
    token, chat_id = get_telegram_config()
    print(f"Sending indicator cheatsheet to chat {chat_id}...")
    send_message(token, chat_id, CHEATSHEET_TEXT)
    print("Done!")


if __name__ == "__main__":
    main()
