# TrendRider — Open-Source Crypto Trading Strategy

[![Strategy](https://img.shields.io/badge/strategy-v2.13.0-00D4AA)](https://github.com/darkvolg/Trading/blob/master/FreqtradeBot/user_data/strategies/TrendRiderStrategy_public.py)
[![Built on](https://img.shields.io/badge/built_on-Freqtrade-blue)](https://github.com/freqtrade/freqtrade)
[![Backtest](https://img.shields.io/badge/backtest_110d-%2B7.29%25-success)](https://trendrider.net/live)
[![Live](https://img.shields.io/badge/live-paper--trading-yellow)](https://trendrider.net/live)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue)](#license)

A multi-indicator confluence strategy for [Freqtrade](https://github.com/freqtrade/freqtrade), running on Bybit USDT-perpetual futures. **Code is open. Numbers are public. Failures are documented.**

🔗 **Live dashboard** → [trendrider.net/live](https://trendrider.net/live) (updates every 5 minutes from the bot's database)

---

## TL;DR

| | Value |
|---|---|
| **Live since** | April 1, 2026 (paper-trading on $500) |
| **Live trades** | 98 closed, +$11.87 (+2.37%), 53.06% win rate |
| **Backtest 110d** (Jan-Apr 2026) | +$36.47 (+7.29%), 37.4% WR, 2.77% max drawdown |
| **Pairs** | 13 USDT-perp (BTC, ETH, SOL, DOGE, XRP, ADA, AVAX, DOT, POL, NEAR, ATOM, SUI, OP) |
| **Timeframe** | 1h candles, ~1.6 trades/day |
| **Risk** | Hyperopt-tuned stoploss (-3.8%), 8 protections, max-open-trades cap |

> **No real money is at risk yet.** This is a public dry-run experiment — paper-trading first, real capital only after a long honest track record.

---

## Why This Repo Is Different

The crypto-bot space is full of black boxes promising 200% APY. This isn't that.

- ✅ **Open source** — every line of strategy code in [`TrendRiderStrategy_public.py`](FreqtradeBot/user_data/strategies/TrendRiderStrategy_public.py). No hidden logic, no API key required to read what it does.
- ✅ **Public live performance** — every trade, every loss, on [trendrider.net/live](https://trendrider.net/live). API serves directly from the bot's SQLite DB. No edits possible.
- ✅ **Honest post-mortems** — [13 days of breakeven trading documented publicly](https://trendrider.net/blog/freqtrade-bot-14-days-breakeven-v4-fix-2026), including the moment one fix turned `-$0.06` into `+$6.42`.
- ✅ **Forward-tested** — backtest results validated on two non-overlapping 55-day windows to rule out curve-fitting. Methodology in [commit `88fb16d`](https://github.com/darkvolg/Trading/commit/88fb16d).
- ✅ **Conservative claims** — backtest projects ~14% annualized on $500. Not life-changing. But realistic.

---

## Strategy Logic (1-minute version)

For each candle, every pair is scored across 8+ technical indicators:

| Indicator | What it measures |
|---|---|
| EMA fast/slow crossover | Trend direction |
| RSI period 19 | Overbought / oversold |
| MACD histogram | Momentum shift |
| ADX threshold 20 | Trend strength |
| Bollinger Bands | Volatility envelope |
| ATR | Volatility magnitude |
| Volume ratio (1.25x avg) | Conviction |
| Market regime classifier | Bull / Bear / Ranging / High-Vol |

Each indicator scores 0-2 points (bear/neutral/bull). Total 0-10. **Trades fire only at confidence ≥6 in bear regime, ≥5 in ranging/bull.**

Exits use a **hyperopt-tuned ROI ladder + custom_exit cascade**:
- `early_loss_cut_2h` — if at -1.5%+ after 2h, kill it
- `early_loss_cut_4h` — if breakeven at 4h, exit
- `early_loss_cut_8h` — if barely positive at 8h, exit
- `early_loss_cut_16h` — last chance
- `time_exit_24h` — hard cap
- `trend_broken` — if EMA crossover reverses, exit
- ROI hits at 6% / 3.5% / 2% / 1% over 0/1h/4h/8h
- Trailing stop on top

---

## Quick Start

Prerequisites: Python 3.10+, Docker (recommended), a Bybit account (testnet for dry-run).

```bash
# 1. Clone this repo
git clone https://github.com/darkvolg/Trading.git
cd Trading/FreqtradeBot

# 2. Install Freqtrade (follow https://www.freqtrade.io/en/stable/installation/)

# 3. Copy config and add your Bybit testnet API keys
cp config.json my-config.json
# Edit my-config.json — set "key" and "secret"

# 4. Download historical data (one-time)
freqtrade download-data --exchange bybit --timeframe 1h \
  --pairs BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT DOGE/USDT:USDT \
  --timerange 20260104-20260423

# 5. Run a backtest to verify the same numbers we publish
freqtrade backtesting --config my-config.json \
  --strategy TrendRiderStrategy --strategy-path user_data/strategies \
  --timerange 20260104-20260423

# 6. Go live in dry-run mode (paper trading)
freqtrade trade --config my-config.json --strategy TrendRiderStrategy
```

Full setup walkthrough: [Freqtrade Tutorial 2026: From Zero to Live Trading Bot](https://trendrider.net/blog/freqtrade-setup-tutorial-beginners-2026)

---

## How to Verify Our Claims

**Don't trust — verify.** Here's how to check every claim on this page yourself:

| Claim | How to verify |
|---|---|
| `+7.29% / 110d backtest` | Clone repo, run backtest command above. Reproduce locally. |
| `+$11.87 / 25d live` | Visit [/live](https://trendrider.net/live) — JSON API at [/api/live-stats.json](https://trendrider.net/api/live-stats.json) updated every 5 min |
| `Forward-tested on halves` | Read commit message of [`88fb16d`](https://github.com/darkvolg/Trading/commit/88fb16d) — full methodology in commit body |
| `No external paid APIs` | Search the strategy file — only TA-Lib indicators, no `requests` calls to paid services |
| `Open-source` | You're reading the source. |

---

## Repo Structure

```
Trading/
├── FreqtradeBot/                      # Bot configuration + strategy
│   ├── config.json                    # Pair whitelist, max trades, exchange
│   └── user_data/strategies/
│       └── TrendRiderStrategy_public.py   # The strategy itself
├── landing/                           # trendrider.net source code (Next.js)
│   ├── app/blog/                      # 50+ articles on bot design, SEO
│   ├── app/live/                      # Public live dashboard
│   └── components/                    # UI
└── README.md                          # This file
```

The strategy file is the only file you need to run the bot. The `landing/` folder is the marketing site source — included for transparency, not required for trading.

---

## Live Performance Methodology

The [/live](https://trendrider.net/live) dashboard is fed by [`scripts/export_live_stats.py`](https://github.com/darkvolg/Trading) (on the production server) which:

1. Reads `tradesv3.dryrun.sqlite` — the bot's SQLite trade log
2. Aggregates: total/closed/open trades, P&L, win rate, exit-reason breakdown
3. Writes JSON to `/var/www/trendrider/api/live-stats.json`
4. Cron runs this every 5 minutes

Numbers can't be massaged — the JSON is direct from the database the bot writes to.

---

## Hyperopt + Forward-Test Methodology

Strategy v2.13.0 was tuned via Freqtrade's hyperopt:

- **Spaces optimized**: buy params, sell params, ROI ladder, trailing stop, stoploss
- **Loss function**: `SharpeHyperOptLoss` (penalizes high-variance returns)
- **Epochs**: 500
- **Time range**: 110 days (Jan 4, 2026 — Apr 23, 2026)

To rule out overfitting, the resulting params were forward-tested on two non-overlapping windows:

| Window | Best previous (V6A) | Hyperopt v2.13.0 |
|---|---|---|
| Jan 4 – Feb 28 (bear half) | −$17.01 | **−$9.40** (smaller loss) |
| Feb 28 – Apr 23 (bull half) | +$36.39 | **+$44.73** (bigger gain) |

Hyperopt won in **both** halves → params are robust, not curve-fit. Full numbers in commit [`88fb16d`](https://github.com/darkvolg/Trading/commit/88fb16d).

---

## Roadmap

- [ ] PR [#334](https://github.com/freqtrade/freqtrade-strategies/pull/334) merged into [`freqtrade/freqtrade-strategies`](https://github.com/freqtrade/freqtrade-strategies)
- [ ] First monthly performance report (end of April 2026)
- [ ] 30 days of live data → switch from $500 paper to $500 real-money
- [ ] Pro Pack: pre-tuned config + monthly hyperopt updates (paid tier)
- [ ] Multi-exchange support (Binance, OKX) — currently Bybit only

---

## Disclaimer

**This is not financial advice.** Past performance does not guarantee future results. Cryptocurrency trading involves substantial risk of loss. Backtests model historical conditions and may not reflect future market behavior. Live results so far are paper-trading only — no real money has been risked.

If you choose to run this strategy with real funds:
- Start with the smallest amount you can afford to lose entirely
- Keep dry-run mode active for at least 30 days first
- Monitor the bot's behavior in your specific market conditions
- Understand that any bot can have a losing streak

---

## Contributing

Issues and PRs welcome. Particularly interested in:
- Bug reports with reproducible scenarios
- Ideas for additional indicators or exit logic (please backtest first)
- Documentation improvements

---

## License

GPL-3.0 — same license as [Freqtrade](https://github.com/freqtrade/freqtrade) itself, the framework this strategy runs on. You're free to use, modify, and redistribute, as long as derivative works remain open-source under the same license.

See [LICENSE](LICENSE) for full text.

---

## Links

- 🌐 Website: [trendrider.net](https://trendrider.net)
- 📊 Live dashboard: [trendrider.net/live](https://trendrider.net/live)
- 📝 Blog: [trendrider.net/blog](https://trendrider.net/blog)
- 💬 Telegram: [@TrendRiderSignals](https://t.me/TrendRiderSignals)
- 🤖 Built on: [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade)
