#!/usr/bin/env python3
"""
Send trading glossary to TrendRider Telegram channel.
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


GLOSSARY_TEXT = """
📖 *Trading Glossary*

Your quick reference for every term used in TrendRider signals\\.

━━━━━━━━━━━━━━━━━━━━━━

• *ADX* — Average Directional Index\\. Measures trend strength \\(0\\-100\\)\\.
• *ATR* — Average True Range\\. Measures volatility\\. Used for dynamic stop\\-loss\\.
• *Bollinger Bands \\(BB\\)* — Volatility bands around moving average\\. Upper/lower bands show overbought/oversold\\.
• *Confidence* — TrendRider's signal quality score \\(1\\-10\\)\\. Higher \\= more indicators aligned\\.
• *DCA* — Dollar Cost Averaging\\. Adding to position at lower prices\\.
• *Drawdown \\(DD\\)* — Peak\\-to\\-trough decline\\. Max DD \\= worst historical decline\\.
• *EMA* — Exponential Moving Average\\. Reacts faster than SMA\\. We use EMA16, 50, 200\\.
• *Entry Zone* — Price range where signal is valid for entry\\.
• *FNG* — Fear \\& Greed Index\\. Market sentiment gauge \\(0\\=extreme fear, 100\\=extreme greed\\)\\.
• *Funding Rate* — Fee paid between longs/shorts on perpetual futures\\. Positive \\= longs pay shorts\\.
• *Invalidation* — Price level where the trade setup is no longer valid\\.
• *Leverage* — Borrowed capital multiplier\\. 3x \\= 3x gains AND 3x losses\\.
• *LONG* — Buying, profiting from price increase\\.
• *MACD* — Moving Average Convergence Divergence\\. Momentum oscillator\\.
• *OI \\(Open Interest\\)* — Total outstanding futures contracts\\. Rising OI \\= new money entering\\.
• *R:R \\(Risk:Reward\\)* — Ratio of potential loss to potential gain\\. 1:2 \\= risk \\$1 to make \\$2\\.
• *Regime* — Market state: Trending Bull, Trending Bear, or Ranging\\.
• *RSI* — Relative Strength Index\\. Momentum indicator \\(0\\-100\\)\\. \\<30 oversold, \\>70 overbought\\.
• *SHORT* — Selling borrowed asset, profiting from price decrease\\.
• *SL \\(Stop Loss\\)* — Auto\\-exit order to limit losses\\.
• *SQN* — System Quality Number\\. Strategy quality metric\\. \\>3 \\= excellent\\.
• *TP \\(Take Profit\\)* — Auto\\-exit order to lock in gains\\.
• *Trailing Stop* — SL that moves up as price rises, locking in profit\\.
• *Volume Ratio* — Current volume vs 20\\-period average\\. \\>1\\.5x \\= high volume confirmation\\.
• *Win Rate \\(WR\\)* — Percentage of profitable trades\\.

━━━━━━━━━━━━━━━━━━━━━━

_Bookmark this post for quick reference\\. Each signal uses these terms — now you know exactly what they mean\\._

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
    print(f"Sending trading glossary to chat {chat_id}...")
    send_message(token, chat_id, GLOSSARY_TEXT)
    print("Done!")


if __name__ == "__main__":
    main()
