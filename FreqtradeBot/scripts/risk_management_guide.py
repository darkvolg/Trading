#!/usr/bin/env python3
"""
Send risk management guide to the TrendRider Telegram channel.
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


RISK_GUIDE_TEXT = """
\U0001f6e1 *Risk Management Guide*

_The difference between profitable traders and blown accounts\\._

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

*1\\. The 1\\-2% Rule*

Never risk more than 1\\-2% of your portfolio on a single trade\\.

Portfolio \\= $10,000
Max risk per trade \\= $100\\-200

This means you survive *50 consecutive losses*
before your account is wiped\\. That\\'s your safety net\\.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

*2\\. Position Sizing Formula*

```
Position Size = Risk Amount / (Entry - Stop Loss)
```

_Example:_
\\> Portfolio: $10,000
\\> Risk: 1% \\= $100
\\> Entry: $64,500 \\| SL: $63,100 \\= $1,400 gap
\\> Position \\= $100 / $1,400 \\* $64,500 \\= *$4,607*

Never guess your size — always calculate\\.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

*3\\. Risk:Reward Ratio*

Always aim for R:R \\> *1:1\\.5*

If risking $100 \\-> target at least $150 profit\\.
TrendRider signals show R:R in every signal\\.

Below 1:1 \\= *skip the trade*\\.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

*4\\. Stop Loss Rules*

\u2022 ALWAYS use SL\\. No exceptions\\.
\u2022 Never move SL *further* from entry
\u2022 After TP1 hit \\-> move SL to breakeven
\u2022 Let trailing stop do its job

_A trade without a stop loss is not a trade — it\\'s a gamble\\._

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

*5\\. Scaling Out*

\u2022 *TP1* \\(\\+3%\\): close 30% — lock profit
\u2022 *TP2* \\(\\+5%\\): close 40% — secure gains
\u2022 *TP3* \\(\\+10%\\): close 30% — ride the trend

This protects against reversals
while capturing upside\\.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

*6\\. Max Exposure*

\u2022 Never have more than *4 positions* open
\u2022 If 3/4 slots filled — be extra selective
\u2022 Correlation matters: BTC\\+ETH count
  as \\~1\\.5 positions due to correlation

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

*7\\. Drawdown Rules*

\u2022 3 consecutive losses \\-> reduce size to 0\\.5%
\u2022 Daily loss \\> 3% \\-> stop trading for the day
\u2022 Weekly loss \\> 5% \\-> review strategy, reduce size

_Protecting capital \\= living to trade another day\\._

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

_Risk management is not optional — it\\'s the ONLY thing that keeps you in the game long\\-term\\. The best traders are the best risk managers\\._

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
    print(f"Sending risk management guide to chat {chat_id}...")
    send_message(token, chat_id, RISK_GUIDE_TEXT)
    print("Done!")


if __name__ == "__main__":
    main()
