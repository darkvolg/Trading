# On-Chain & Derivatives Data Sources for TrendRiderStrategy

**Date**: 2026-03-21
**Context**: Bybit USDT perpetual futures, 1h timeframe, trend-following, leverage 3x

---

## 1. Bybit API v5 — Native Data (FREE, no key needed for public endpoints)

Bybit already provides everything you need for derivatives metrics **for free** via public market endpoints. No API key required for read-only data.

### Available Endpoints (all free, no auth)

| Endpoint | Data | URL |
|---|---|---|
| `/v5/market/funding/history` | Historical funding rates | public |
| `/v5/market/open-interest` | OI history (5min/1h/4h/1d) | public |
| `/v5/market/insurance` | Insurance fund history | public |
| WebSocket: `allLiquidation.{symbol}` | Real-time liquidations | public WS |

### Python example — pull funding rate + OI directly:

```python
import requests

def get_bybit_funding_rate(symbol: str = "BTCUSDT") -> float:
    """Returns latest funding rate (e.g., 0.0001 = 0.01%)"""
    url = "https://api.bybit.com/v5/market/funding/history"
    params = {"category": "linear", "symbol": symbol, "limit": 1}
    r = requests.get(url, params=params, timeout=5)
    data = r.json()["result"]["list"]
    if data:
        return float(data[0]["fundingRate"])
    return 0.0

def get_bybit_open_interest(symbol: str = "BTCUSDT") -> float:
    """Returns latest OI in contracts"""
    url = "https://api.bybit.com/v5/market/open-interest"
    params = {"category": "linear", "symbol": symbol, "intervalTime": "1h", "limit": 2}
    r = requests.get(url, params=params, timeout=5)
    data = r.json()["result"]["list"]
    if len(data) >= 2:
        oi_now = float(data[0]["openInterest"])
        oi_prev = float(data[1]["openInterest"])
        return oi_now, oi_now - oi_prev  # (current, delta)
    return 0.0, 0.0
```

### Liquidations — WebSocket only (Bybit)

Bybit pushes liquidations via WebSocket, not REST. This means:
- REST: you can get recent liquidation snapshots via `/v5/market/recent-trade` indirectly — no direct liquidation REST endpoint.
- WebSocket: `allLiquidation.{symbol}` topic, push every 500ms.

**Recommendation**: For Freqtrade, use pybit WebSocket in `bot_loop_start()` to accumulate liquidation volume per hour into a rolling counter.

```python
from pybit.unified_trading import WebSocket

# In strategy __init__:
self._liq_long_1h = {}   # {pair: float}  cumulative LONG liquidations last 1h
self._liq_short_1h = {}  # {pair: float}  cumulative SHORT liquidations last 1h
```

---

## 2. CoinGlass API — Aggregated Multi-Exchange Data

CoinGlass aggregates funding rates, OI, and liquidations from **all major exchanges** (Binance, OKX, Bybit, Deribit, etc.). This gives a broader market picture than Bybit alone.

### Pricing Reality (2026)

- **No free tier with API access** — the website shows free dashboards, but API access requires a paid plan.
- **Cheapest plan**: ~$29/month (Hobbyist) — gives 80+ endpoints, 300 req/day limit.
- **Relevant for**: multi-exchange OI aggregation, liquidation heatmaps, institutional data.

### Python client (community):

```bash
pip install coinglass-api  # or pip install coinglass-apiv3 for v3 API
```

```python
from coinglass_api import CoinglassAPI

cg = CoinglassAPI(api_key="YOUR_KEY")
# funding rate history for BTC across all exchanges
df_funding = cg.funding_rate_ohlc(symbol="BTC", exchange="Bybit", interval="1h")
# open interest
df_oi = cg.open_interest_ohlc(symbol="BTC", exchange="Bybit", interval="1h")
```

**Verdict**: Not free. Use Bybit API directly (free) for single-exchange data.

---

## 3. Whale Tracking — Realistic Options

### Option A: Whale Alert (PAID for API)

- Website/Twitter: free alerts.
- API: from $49/month (Developer tier).
- **Not practical** for automated trading — too expensive, too noisy for 1h futures.

### Option B: ClankApp (FREE API)

- Tracks large transactions on 24+ blockchains.
- REST API available, free tier exists.
- URL: https://clankapp.com/api/v2/transactions
- Data: wallet transfers >$1M on-chain.

```python
import requests

def get_clankapp_whale_alerts(chain: str = "ethereum", min_usd: int = 1_000_000) -> list:
    url = "https://api.clankapp.com/v2/t"
    params = {"chain": chain, "s_amount_usd": min_usd, "size": 10, "sort": "desc"}
    r = requests.get(url, params=params, timeout=5)
    return r.json().get("data", {}).get("transactions", [])
```

**Caveats**: On-chain whale transfers have very weak signal for 1h futures trading (see Section 7).

### Option C: Arkham Intelligence (FREE web, no automation API)

- Excellent free dashboard for manual research.
- No programmatic API for automated trading (as of 2026).
- Use for research, not live signals.

---

## 4. Exchange Netflow Data — Free Sources

Exchange netflow (coins entering/leaving exchanges) is a **macro/daily signal**, not useful for 1h trading. But here are free sources:

### CryptoMeter.io

- Free real-time netflow charts.
- No documented public API — scraping only (fragile).

### The Block (theblock.co)

- Free historical charts for BTC/ETH/USDT flows.
- No free API — data exports require paid plan.

### Glassnode / CryptoQuant

- Both require paid API access ($39-$99/month minimum).

**Verdict**: Exchange netflow is a daily/weekly signal and doesn't integrate well into 1h Freqtrade strategy. Skip for now.

---

## 5. Python Libraries Summary

| Library | Purpose | Free? | Quality |
|---|---|---|---|
| `pybit` | Official Bybit API (REST + WS) | Yes | Excellent |
| `requests` | Direct Bybit REST calls | Yes | Simple, reliable |
| `coinglass-api` (PyPI) | CoinGlass wrapper | No (API key $29/mo) | Good |
| `coinglass-apiv3` (PyPI) | CoinGlass v3 wrapper | No | Good |
| `web3.py` | Direct Ethereum node access | Yes (node required) | Complex |
| `clankapp` (manual requests) | Whale transactions | Yes (free tier) | Noisy |

**For your use case**: `pybit` + direct `requests` to Bybit covers 95% of what you need, for free.

```bash
pip install pybit requests
```

---

## 6. Integration Pattern into Freqtrade

### Architecture: Two-layer approach

```
bot_loop_start()      → Fetch external data every N minutes, store in self._cache
populate_indicators() → Read from self._cache, add columns to dataframe
```

### Why NOT fetch in `populate_indicators()` directly?

- `populate_indicators()` runs per pair, per candle refresh — too many API calls.
- In backtesting, it runs on historical data — external API would return current data, invalidating backtest.
- The cache pattern in `bot_loop_start()` solves both problems.

### Recommended Implementation

```python
import requests
from datetime import datetime, timezone, timedelta
from freqtrade.strategy import IStrategy
from pandas import DataFrame

class TrendRiderStrategy(IStrategy):

    # Cache storage
    _derivatives_cache: dict = {}   # {symbol: {funding_rate, oi, oi_delta, ts}}
    _cache_ttl_minutes: int = 5     # Refresh every 5 minutes

    def bot_loop_start(self, current_time: datetime, **kwargs) -> None:
        """Fetch derivatives data once per 5-minute cycle."""
        pairs = self.dp.current_whitelist() if self.dp else []

        for pair in pairs:
            # Convert CCXT pair format to Bybit symbol: "BTC/USDT:USDT" -> "BTCUSDT"
            symbol = pair.split("/")[0] + "USDT"

            # Check cache freshness
            cached = self._derivatives_cache.get(symbol, {})
            ts = cached.get("ts")
            if ts and (current_time - ts).total_seconds() < self._cache_ttl_minutes * 60:
                continue  # Still fresh

            try:
                funding = self._fetch_funding_rate(symbol)
                oi, oi_delta = self._fetch_open_interest(symbol)
                self._derivatives_cache[symbol] = {
                    "funding_rate": funding,
                    "open_interest": oi,
                    "oi_delta": oi_delta,
                    "ts": current_time,
                }
            except Exception as e:
                logger.warning(f"Derivatives fetch failed for {symbol}: {e}")

    def _fetch_funding_rate(self, symbol: str) -> float:
        url = "https://api.bybit.com/v5/market/funding/history"
        r = requests.get(url, params={"category": "linear", "symbol": symbol, "limit": 1}, timeout=5)
        data = r.json().get("result", {}).get("list", [])
        return float(data[0]["fundingRate"]) if data else 0.0

    def _fetch_open_interest(self, symbol: str) -> tuple:
        url = "https://api.bybit.com/v5/market/open-interest"
        r = requests.get(url, params={
            "category": "linear", "symbol": symbol, "intervalTime": "1h", "limit": 2
        }, timeout=5)
        data = r.json().get("result", {}).get("list", [])
        if len(data) >= 2:
            oi_now = float(data[0]["openInterest"])
            oi_prev = float(data[1]["openInterest"])
            return oi_now, (oi_now - oi_prev) / oi_prev if oi_prev > 0 else 0.0
        return 0.0, 0.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ... existing indicators ...

        # Add derivatives data from cache (safe: defaults to 0 in backtest)
        symbol = metadata["pair"].split("/")[0] + "USDT"
        cache = self._derivatives_cache.get(symbol, {})

        # These will be constant columns (same value for all rows in live mode)
        # In backtest: always 0.0 — acceptable, disable conditions using them in backtest
        dataframe["funding_rate"] = cache.get("funding_rate", 0.0)
        dataframe["oi_delta_pct"] = cache.get("oi_delta", 0.0)

        return dataframe
```

### Important: Backtest Safety

External data in `populate_indicators` breaks backtesting because it injects current values into historical candles. Solutions:

**Option 1** — Disable conditions in backtest (simplest):
```python
# In populate_entry_trend:
is_live = self.dp.runmode.value in ('live', 'dry_run')

if is_live:
    conditions += [
        dataframe["funding_rate"] < 0.0003,   # Not overheated longs
        dataframe["oi_delta_pct"] > -0.05,    # OI not collapsing
    ]
```

**Option 2** — Separate signal file (complex, robust):
Pre-download historical funding rates from Bybit REST (which has full history), merge as a CSV, load in `__init__`. Bybit keeps funding rate history going back 2+ years.

---

## 7. Realistic Assessment: What Actually Helps for 1h Futures Trading

### HIGH SIGNAL VALUE — Use these

#### 1. Funding Rate (from Bybit, FREE)
- **Why it works**: Extreme positive funding (>0.03% per 8h = 0.1% daily) means the market is heavily long. These conditions precede sharp reversals or at minimum, increased volatility.
- **Practical use**: Filter entries when funding is extremely elevated. Not a reversal signal by itself, but a risk filter.
- **Threshold**: `funding_rate > 0.0003` (0.03% = 3x normal) = caution, reduce size or skip.
- **Bybit normal rate**: 0.01% per 8h. Anything above 0.03% is elevated.

```python
# Entry filter: avoid entering when market is overleveraged long
dataframe["funding_extreme"] = (dataframe["funding_rate"] > 0.0003).astype(int)
# Block entries during extreme funding
conditions += [dataframe["funding_extreme"] == 0]
```

#### 2. Open Interest Delta (from Bybit, FREE)
- **Why it works**: OI rising with price = new money entering = trend confirmation. OI falling with price = deleveraging, trend weak.
- **Practical use**: Confirm trend entries when OI is rising.
- **Threshold**: `oi_delta_pct > 0.02` (OI grew 2%+ last hour) = strong conviction.

```python
# Confirm entry: OI growing supports trend
dataframe["oi_growing"] = (dataframe["oi_delta_pct"] > 0.01).astype(int)
```

### MEDIUM SIGNAL VALUE — Consider with caution

#### 3. Liquidation Cascades (Bybit WebSocket)
- **Why it works**: Large liquidation clusters near current price = magnet zones. After a cascade, volatility spikes then reverts.
- **Practical use**: Avoid entering immediately after a large cascade (price unstable). Or enter after cascade completes (volatility exhaustion entry).
- **Implementation complexity**: Requires WebSocket accumulator, harder to maintain. Moderate value for 1h strategy.

#### 4. BTC Funding Rate as Market Sentiment
- **Why it works**: When BTC funding is negative (longs being paid), market is fearful — good entry for contrarian longs in existing uptrend.
- Already partially addressed by your `btc_rsi_1h` filter — complementary, not replacement.

### LOW SIGNAL VALUE for 1h Futures — Skip these

#### On-Chain Whale Transfers (ClankApp, etc.)
- Whale moves large BTC on-chain → usually exchange deposits → could mean selling intent.
- **Problem**: Signal lag is 1-24 hours. On 1h charts, by the time you detect it, the move is priced in.
- **Verdict**: Skip. Too noisy, too slow.

#### Exchange Netflow (CryptoQuant, etc.)
- Meaningful on daily/weekly charts.
- On 1h chart: irrelevant. Move takes days to materialize.
- **Verdict**: Skip entirely.

#### Glassnode SOPR, NUPL, MVRV
- Pure on-chain metrics. Useful for macro positioning (weeks/months).
- Completely useless for 1h trading.
- **Verdict**: Skip.

---

## 8. Recommended Minimal Implementation

### Priority order (by effort vs. value):

**Phase 1 — Immediate, 2 hours work**:
- Bybit funding rate filter in `populate_entry_trend()` via `bot_loop_start()` cache.
- Block entries when funding > 0.03% (market overheated).
- Cost: $0. Library: `requests` (already installed).

**Phase 2 — 1 day work, moderate gain**:
- Add OI delta as trend confirmation signal.
- `oi_delta_pct > 1%` confirms trend momentum.
- Cost: $0.

**Phase 3 — Optional, significant effort**:
- WebSocket liquidation accumulator for the pairs you trade.
- Useful if you find entries are hitting liquidation cascade spikes.
- Cost: $0, but adds complexity to maintain.

### Minimum code to add to TrendRiderStrategy

The smallest meaningful addition (funding rate filter only):

```python
# In __init__:
self._funding_cache: dict = {}  # {symbol: (rate, timestamp)}

# Add to bot_loop_start() after existing price alert logic:
for pair in self.dp.current_whitelist():
    symbol = pair.split("/")[0] + "USDT"
    cached_ts = self._funding_cache.get(symbol, (0.0, None))[1]
    if cached_ts and (current_time - cached_ts).total_seconds() < 300:
        continue
    try:
        url = "https://api.bybit.com/v5/market/funding/history"
        r = requests.get(url, params={"category": "linear", "symbol": symbol, "limit": 1}, timeout=3)
        rate = float(r.json()["result"]["list"][0]["fundingRate"])
        self._funding_cache[symbol] = (rate, current_time)
    except Exception:
        pass

# In populate_indicators():
symbol = metadata["pair"].split("/")[0] + "USDT"
funding_rate, _ = self._funding_cache.get(symbol, (0.0, None))
dataframe["funding_rate"] = funding_rate
dataframe["funding_extreme"] = (dataframe["funding_rate"] > 0.0003).astype(int)

# In populate_entry_trend(), add to each conditions list:
# (only in live/dry_run mode to not break backtests)
if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
    conditions_pullback.append(dataframe["funding_extreme"] == 0)
    conditions_ema50.append(dataframe["funding_extreme"] == 0)
    conditions_rsi.append(dataframe["funding_extreme"] == 0)
```

### What to expect from this addition

- **Expected effect**: Filters 5-15% of entries during overheated market conditions. These are typically the worst entries (buying near tops when everyone is already long).
- **Backtest impact**: None — condition bypassed in backtest mode.
- **Live effect**: Avoids the "crowded long" setups that tend to reverse sharply.
- **Risk**: False negatives — sometimes funding is high and price continues up. Use as filter, not as primary signal.

---

## 9. Summary Table

| Metric | Source | Cost | Signal for 1h | Integration |
|---|---|---|---|---|
| Funding Rate | Bybit API v5 | Free | HIGH — risk filter | bot_loop_start cache |
| Open Interest | Bybit API v5 | Free | MEDIUM — trend confirm | bot_loop_start cache |
| Liquidations (own exchange) | Bybit WebSocket | Free | MEDIUM — cascade detect | WebSocket accumulator |
| Multi-exchange OI/Funding | CoinGlass | $29/mo | MEDIUM+ | coinglass-api lib |
| Whale on-chain transfers | ClankApp | Free | LOW — too slow | Not recommended |
| Exchange netflow | CryptoQuant/Glassnode | $39-99/mo | VERY LOW for 1h | Not recommended |
| SOPR/MVRV/NUPL | Glassnode | $99+/mo | ZERO for 1h | Skip entirely |

---

## Sources

- [Bybit v5 Funding Rate History](https://bybit-exchange.github.io/docs/v5/market/history-fund-rate)
- [Bybit v5 Open Interest](https://bybit-exchange.github.io/docs/v5/market/open-interest)
- [Bybit v5 All Liquidation WebSocket](https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation)
- [pybit GitHub (official Bybit Python client)](https://github.com/bybit-exchange/pybit)
- [CoinGlass API Documentation](https://docs.coinglass.com/)
- [CoinGlass Pricing](https://www.coinglass.com/pricing)
- [coinglass-api PyPI](https://pypi.org/project/coinglass-api/)
- [ClankApp Whale Tracker](https://clankapp.com/)
- [Funding Rates as Trading Signals — QuantJourney](https://quantjourney.substack.com/p/funding-rates-in-crypto-the-hidden)
- [Funding Rate + OI: How to Spot Liquidations](https://tradelink.pro/blog/funding-rate-open-interest/)
- [Gate.io: How OI, Funding Rate, Liquidation signal trends](https://web3.gate.com/crypto-wiki/article/how-do-futures-open-interest-funding-rates-and-liquidation-data-signal-derivatives-market-trends-20260109)
- [Freqtrade Strategy Customization Docs](https://www.freqtrade.io/en/stable/strategy-customization/)
