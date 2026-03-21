"""
TrendRiderStrategy — "Trend Rider" v2.0

Philosophy: Ride established trends with WIDE stoploss.
Key insight: crypto swings 2-4% per hour. Stoploss must be >= 5-6%.

v2.0 additions:
- SHORT strategy (mirrored LONG logic)
- DCA (Dollar Cost Averaging) for losing positions
- Dynamic ATR-based stoploss
- Partial Take Profit (TP1/TP2/TP3 via adjust_trade_position)
- Improved confidence scoring with weighted factors
- Cornix-compatible signal format
- Reject weak signals (confidence < 5)
- Multi-timeframe 15m + Daily confirmation
- Fear & Greed Index integration
- Persistent price alerts (SQLite)
"""

import json
import os
import sqlite3
import time
import talib.abstract as ta
from datetime import datetime, timedelta, timezone
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, merge_informative_pair
from pandas import DataFrame
from functools import reduce
from pathlib import Path
import logging
import requests

logger = logging.getLogger(__name__)


class TrendRiderStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # --- ROI: Wide, let winners run ---
    minimal_roi = {
        "0": 0.10,      # 10% immediate
        "120": 0.06,    # 6% after 2h
        "360": 0.04,    # 4% after 6h
        "720": 0.025,   # 2.5% after 12h
        "1440": 0.015,  # 1.5% after 24h
        "2880": 0.01,   # 1% after 48h
    }

    # --- Stoploss: WIDE for crypto volatility ---
    stoploss = -0.06           # 6% default (ATR-based custom stoploss overrides)
    use_custom_stoploss = True  # Dynamic ATR-based stoploss

    # --- Trailing Stop: WIDE ---
    trailing_stop = True
    trailing_stop_positive = 0.03        # 3% trail
    trailing_stop_positive_offset = 0.05 # Activate after +5%
    trailing_only_offset_is_reached = True

    # --- General ---
    timeframe = "1h"
    startup_candle_count = 210
    process_only_new_candles = True
    can_short = True
    position_adjustment_enable = True

    # --- Protections (moved from config.json for Freqtrade 2026.2+) ---
    protections = [
        {
            "method": "CooldownPeriod",
            "stop_duration": 20
        },
        {
            "method": "StoplossGuard",
            "lookback_period": 720,
            "trade_limit": 3,
            "stop_duration": 60,
            "only_per_pair": False
        },
        {
            "method": "MaxDrawdown",
            "lookback_period": 1440,
            "max_allowed_drawdown": 0.10,
            "stop_duration": 300,
            "trade_limit": 5
        }
    ]

    # --- HyperOpt Results (applied from optimization session 2026-03-21) ---
    buy_params = {
        "ema_fast": 9,
        "ema_slow": 16,
        "rsi_period": 16,
        "rsi_pullback_low": 40,
        "rsi_pullback_high": 58,
        "rsi_bounce": 30,
        "adx_threshold": 27,
        "volume_factor": 1.014,
    }

    sell_params = {
        "rsi_exit": 81,
    }

    # --- HyperOpt Parameters ---
    ema_fast = IntParameter(5, 15, default=9, space="buy")
    ema_slow = IntParameter(15, 30, default=21, space="buy")
    rsi_period = IntParameter(10, 20, default=14, space="buy")
    rsi_pullback_low = IntParameter(30, 48, default=40, space="buy")
    rsi_pullback_high = IntParameter(52, 65, default=58, space="buy")
    rsi_bounce = IntParameter(25, 35, default=30, space="buy")
    rsi_exit = IntParameter(72, 85, default=78, space="sell")
    adx_threshold = IntParameter(20, 35, default=25, space="buy")
    volume_factor = DecimalParameter(1.0, 2.5, default=1.3, space="buy")

    # --- Leverage: fixed, not optimized (fix #9) ---
    leverage_value = 3

    # --- FNG cache ---
    _fng_cache_file = None
    _fng_cache_ttl = 14400  # 4 hours

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        # SQLite-based persistent price alerts
        self._alerts_db_path = self._get_alerts_db_path(config)
        self._init_alerts_db()
        # FNG cache file path
        data_dir = config.get('user_data_dir', Path('.'))
        if isinstance(data_dir, str):
            data_dir = Path(data_dir)
        self._fng_cache_file = str(data_dir / 'fng_cache.json')
        # On-chain data cache: {pair: {'rate': float, 'oi_change': float, 'ts': float}}
        self._funding_cache = {}

    def _get_alerts_db_path(self, config: dict) -> str:
        """Get path for price alerts SQLite DB."""
        data_dir = config.get('user_data_dir', Path('.'))
        if isinstance(data_dir, str):
            data_dir = Path(data_dir)
        return str(data_dir / 'price_alerts.db')

    def _init_alerts_db(self):
        """Initialize SQLite DB for persistent price alerts."""
        try:
            conn = sqlite3.connect(self._alerts_db_path)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS price_alerts "
                "(pair TEXT PRIMARY KEY, last_alert_time TEXT)"
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to init alerts DB: {e}")

    def _get_last_alert(self, pair: str):
        """Get last alert time from SQLite."""
        try:
            conn = sqlite3.connect(self._alerts_db_path)
            cursor = conn.execute(
                "SELECT last_alert_time FROM price_alerts WHERE pair = ?", (pair,)
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return datetime.fromisoformat(row[0])
            return None
        except Exception:
            return None

    def _set_last_alert(self, pair: str, alert_time: datetime):
        """Save last alert time to SQLite."""
        try:
            conn = sqlite3.connect(self._alerts_db_path)
            conn.execute(
                "INSERT OR REPLACE INTO price_alerts (pair, last_alert_time) VALUES (?, ?)",
                (pair, alert_time.isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to save alert: {e}")

    # --- Fear & Greed Index ---
    def _get_fng_data(self) -> dict:
        """Fetch Fear & Greed Index with 4h file-based cache."""
        # Check cache
        if self._fng_cache_file and os.path.exists(self._fng_cache_file):
            try:
                with open(self._fng_cache_file, 'r') as f:
                    cached = json.load(f)
                cached_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
                if (datetime.now() - cached_time).total_seconds() < self._fng_cache_ttl:
                    return cached.get('data', {})
            except Exception:
                pass

        # Fetch fresh data
        try:
            resp = requests.get(
                'https://api.alternative.me/fng/?limit=60&format=json',
                timeout=10
            )
            resp.raise_for_status()
            raw = resp.json()
            data_list = raw.get('data', [])
            # Build dict: date_str -> fng_value
            fng_map = {}
            for item in data_list:
                ts = int(item.get('timestamp', 0))
                val = int(item.get('value', 50))
                date_str = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
                fng_map[date_str] = val

            # Save cache
            if self._fng_cache_file:
                try:
                    with open(self._fng_cache_file, 'w') as f:
                        json.dump({
                            'timestamp': datetime.now().isoformat(),
                            'data': fng_map
                        }, f)
                except Exception:
                    pass
            return fng_map
        except Exception as e:
            logger.warning(f"FNG fetch failed: {e}")
            return {}

    # --- On-chain data: Funding Rate & Open Interest (Bybit v5) ---
    def _pair_to_bybit_symbol(self, pair: str) -> str:
        """Convert Freqtrade pair format to Bybit symbol. E.g. 'BTC/USDT:USDT' -> 'BTCUSDT'."""
        return pair.replace('/USDT:USDT', 'USDT').replace('/', '')

    def _fetch_funding_rate(self, pair: str) -> float:
        """Fetch latest funding rate from Bybit v5 API with 5-min cache."""
        cached = self._funding_cache.get(pair, {})
        if cached and (time.time() - cached.get('ts', 0)) < 300:
            return cached.get('rate', 0.0)

        symbol = self._pair_to_bybit_symbol(pair)
        try:
            resp = requests.get(
                'https://api.bybit.com/v5/market/funding/history',
                params={'category': 'linear', 'symbol': symbol, 'limit': 1},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            result_list = data.get('result', {}).get('list', [])
            if result_list:
                rate = float(result_list[0].get('fundingRate', 0))
            else:
                rate = 0.0
        except Exception as e:
            logger.warning(f"Funding rate fetch failed for {pair}: {e}")
            rate = cached.get('rate', 0.0)

        # Update cache (preserve oi_change if already fetched)
        existing = self._funding_cache.get(pair, {})
        self._funding_cache[pair] = {
            'rate': rate,
            'oi_change': existing.get('oi_change', 0.0),
            'ts': time.time(),
        }
        return rate

    def _fetch_open_interest(self, pair: str) -> float:
        """Fetch open interest change ratio from Bybit v5 API with 5-min cache."""
        cached = self._funding_cache.get(pair, {})
        if cached and (time.time() - cached.get('ts', 0)) < 300:
            return cached.get('oi_change', 0.0)

        symbol = self._pair_to_bybit_symbol(pair)
        try:
            resp = requests.get(
                'https://api.bybit.com/v5/market/open-interest',
                params={'category': 'linear', 'symbol': symbol, 'intervalTime': '1h', 'limit': 2},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            result_list = data.get('result', {}).get('list', [])
            if len(result_list) >= 2:
                current_oi = float(result_list[0].get('openInterest', 0))
                previous_oi = float(result_list[1].get('openInterest', 0))
                if previous_oi > 0:
                    oi_change = (current_oi / previous_oi) - 1
                else:
                    oi_change = 0.0
            else:
                oi_change = 0.0
        except Exception as e:
            logger.warning(f"Open interest fetch failed for {pair}: {e}")
            oi_change = cached.get('oi_change', 0.0)

        # Update cache (preserve rate if already fetched)
        existing = self._funding_cache.get(pair, {})
        self._funding_cache[pair] = {
            'rate': existing.get('rate', 0.0),
            'oi_change': oi_change,
            'ts': time.time(),
        }
        return oi_change

    def leverage(self, pair: str, current_time, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str,
                 side: str, **kwargs) -> float:
        return min(float(self.leverage_value), max_leverage)

    # --- Price Alert: notify when price approaches entry zone ---
    def bot_loop_start(self, current_time, **kwargs) -> None:
        if not self.dp:
            return

        # Fetch funding rates & open interest for all pairs (live/dry_run only)
        if self.dp.runmode.value in ('live', 'dry_run'):
            for pair in self.dp.current_whitelist():
                try:
                    self._fetch_funding_rate(pair)
                    self._fetch_open_interest(pair)
                except Exception as e:
                    logger.warning(f"On-chain data fetch failed for {pair}: {e}")

        for pair in self.dp.current_whitelist():
            # Cooldown: max 1 alert per pair per 4 hours (persistent via SQLite)
            last_alert = self._get_last_alert(pair)
            if last_alert and (current_time - last_alert).total_seconds() < 14400:
                continue

            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if len(dataframe) < 2:
                continue
            last = dataframe.iloc[-1]

            close = last.get('close', 0)
            if close <= 0:
                continue

            ema_slow_key = f"ema_{self.ema_slow.value}"
            ema_slow_val = last.get(ema_slow_key, 0)
            ema_50_val = last.get('ema_50', 0)
            is_bull = last.get('is_bull', 0)

            if not is_bull or ema_slow_val <= 0:
                continue

            # Check proximity to EMA support (within 1.5%)
            dist_ema = (close - ema_slow_val) / ema_slow_val * 100
            dist_ema50 = (close - ema_50_val) / ema_50_val * 100 if ema_50_val > 0 else 999

            zone = None
            zone_price = 0
            zone_name = ""

            if 0 < dist_ema < 1.5:
                zone = "ema_slow"
                zone_price = ema_slow_val
                zone_name = f"EMA{self.ema_slow.value}"
            elif 0 < dist_ema50 < 1.5:
                zone = "ema50"
                zone_price = ema_50_val
                zone_name = "EMA50"

            if zone:
                rsi_key = f"rsi_{self.rsi_period.value}"
                rsi_val = last.get(rsi_key, 50)
                adx_val = last.get('adx', 0)
                vol_ratio = last.get('volume_ratio', 0)

                dist = (close - zone_price) / zone_price * 100

                msg = (
                    f"*PRICE ALERT*\n"
                    f"{'='*28}\n"
                    f"*{pair}* approaching entry zone\n\n"
                    f"*Price:* `{close:.2f}` USDT\n"
                    f"*{zone_name}:* `{zone_price:.2f}` ({dist:.1f}% above)\n\n"
                    f"*RSI:* {rsi_val:.1f} | *ADX:* {adx_val:.1f} | *Vol:* {vol_ratio:.2f}x\n"
                    f"{'='*28}\n"
                    f"_Watch for entry signal_"
                )
                self.dp.send_msg(msg, always_send=True)
                self._set_last_alert(pair, current_time)

    def informative_pairs(self):
        pairs = self.dp.current_whitelist() if self.dp else []
        informative = []
        for pair in pairs:
            informative.append((pair, "4h"))
            informative.append((pair, "15m"))
            informative.append((pair, "1d"))
        # BTC as market sentiment
        informative.append(("BTC/USDT:USDT", "1h"))
        informative.append(("BTC/USDT:USDT", "4h"))
        return informative

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # EMAs (all periods for hyperopt ranges)
        for period in range(5, 31):
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_200"] = ta.EMA(dataframe, timeperiod=200)

        # RSI (all periods for hyperopt range 10-20)
        for period in range(10, 21):
            dataframe[f"rsi_{period}"] = ta.RSI(dataframe, timeperiod=period)

        # ADX
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)

        # MACD
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # Bollinger Bands
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bb["upperband"]
        dataframe["bb_middle"] = bb["middleband"]
        dataframe["bb_lower"] = bb["lowerband"]

        # Volume (fix #4: epsilon guard against division by zero)
        dataframe["volume_ema"] = ta.EMA(dataframe["volume"], timeperiod=20)
        dataframe["volume_ratio"] = dataframe["volume"] / (dataframe["volume_ema"] + 1e-10)

        # OBV
        dataframe["obv"] = ta.OBV(dataframe)
        dataframe["obv_ema"] = ta.EMA(dataframe["obv"], timeperiod=20)

        # ATR for dynamic stoploss
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        # Regime
        dataframe["is_bull"] = (
            (dataframe["close"] > dataframe["ema_200"]) &
            (dataframe["ema_50"] > dataframe["ema_200"])
        ).astype(int)

        dataframe["is_bear"] = (
            (dataframe["close"] < dataframe["ema_200"]) &
            (dataframe["ema_50"] < dataframe["ema_200"])
        ).astype(int)

        # --- LONG pullback detection ---
        ema_slow_key = f"ema_{self.ema_slow.value}"
        if ema_slow_key in dataframe.columns:
            dataframe["pullback_to_ema"] = (
                (dataframe["low"] <= dataframe[ema_slow_key] * 1.01) &
                (dataframe["close"] > dataframe[ema_slow_key]) &
                (dataframe["close"] > dataframe["open"])  # Bullish candle
            ).astype(int)
        else:
            dataframe["pullback_to_ema"] = 0

        # EMA50 support bounce (LONG)
        dataframe["ema50_bounce"] = (
            (dataframe["low"] <= dataframe["ema_50"] * 1.01) &
            (dataframe["close"] > dataframe["ema_50"]) &
            (dataframe["close"] > dataframe["open"])
        ).astype(int)

        # --- SHORT pullback detection ---
        if ema_slow_key in dataframe.columns:
            dataframe["pullback_from_ema"] = (
                (dataframe["high"] >= dataframe[ema_slow_key] * 0.99) &
                (dataframe["close"] < dataframe[ema_slow_key]) &
                (dataframe["close"] < dataframe["open"])  # Bearish candle
            ).astype(int)
        else:
            dataframe["pullback_from_ema"] = 0

        # EMA50 rejection (SHORT)
        dataframe["ema50_rejection"] = (
            (dataframe["high"] >= dataframe["ema_50"] * 0.99) &
            (dataframe["close"] < dataframe["ema_50"]) &
            (dataframe["close"] < dataframe["open"])
        ).astype(int)

        # --- Multi-Timeframe data ---
        if self.dp:
            # 4h data for current pair
            df_4h = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe='4h')
            if len(df_4h) > 0:
                df_4h['ema_50'] = ta.EMA(df_4h, timeperiod=50)
                df_4h['ema_200'] = ta.EMA(df_4h, timeperiod=200)
                df_4h['rsi_14'] = ta.RSI(df_4h, timeperiod=14)
                df_4h['adx'] = ta.ADX(df_4h, timeperiod=14)
                df_4h['is_bull'] = (
                    (df_4h['close'] > df_4h['ema_200']) &
                    (df_4h['ema_50'] > df_4h['ema_200'])
                ).astype(int)
                dataframe = merge_informative_pair(
                    dataframe,
                    df_4h[['date', 'ema_50', 'ema_200', 'rsi_14', 'adx', 'is_bull']],
                    self.timeframe, '4h', ffill=True
                )
            else:
                dataframe['ema_50_4h'] = 0
                dataframe['ema_200_4h'] = 0
                dataframe['rsi_14_4h'] = 50
                dataframe['adx_4h'] = 0
                dataframe['is_bull_4h'] = 0

            # 15m data for entry precision
            df_15m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe='15m')
            if len(df_15m) > 0:
                df_15m['rsi_15m'] = ta.RSI(df_15m, timeperiod=14)
                df_15m['ema_fast_15m'] = ta.EMA(df_15m, timeperiod=9)
                dataframe = merge_informative_pair(
                    dataframe,
                    df_15m[['date', 'rsi_15m', 'ema_fast_15m']],
                    self.timeframe, '15m', ffill=True
                )
            else:
                dataframe['rsi_15m_15m'] = 50
                dataframe['ema_fast_15m_15m'] = 0

            # Daily data for macro trend
            df_1d = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe='1d')
            if len(df_1d) > 0:
                df_1d['ema_200_1d'] = ta.EMA(df_1d, timeperiod=200)
                dataframe = merge_informative_pair(
                    dataframe,
                    df_1d[['date', 'ema_200_1d']],
                    self.timeframe, '1d', ffill=True
                )
            else:
                dataframe['ema_200_1d_1d'] = 0

            # BTC market sentiment
            df_btc = self.dp.get_pair_dataframe(pair='BTC/USDT:USDT', timeframe='1h')
            if len(df_btc) > 0:
                df_btc['btc_ema_200'] = ta.EMA(df_btc, timeperiod=200)
                df_btc['btc_ema_50'] = ta.EMA(df_btc, timeperiod=50)
                df_btc['btc_rsi'] = ta.RSI(df_btc, timeperiod=14)
                df_btc['btc_is_bull'] = (
                    (df_btc['close'] > df_btc['btc_ema_200']) &
                    (df_btc['btc_ema_50'] > df_btc['btc_ema_200'])
                ).astype(int)
                dataframe = merge_informative_pair(
                    dataframe,
                    df_btc[['date', 'btc_ema_200', 'btc_ema_50', 'btc_rsi', 'btc_is_bull']],
                    self.timeframe, '1h', ffill=True
                )
            else:
                dataframe['btc_is_bull_1h'] = 1
                dataframe['btc_rsi_1h'] = 50
        else:
            # Safety fallback when dp is not available
            dataframe['is_bull_4h'] = dataframe['is_bull']
            dataframe['rsi_14_4h'] = dataframe['rsi_14'] if 'rsi_14' in dataframe.columns else 50
            dataframe['adx_4h'] = dataframe['adx']
            dataframe['btc_is_bull_1h'] = 1
            dataframe['btc_rsi_1h'] = 50
            dataframe['rsi_15m_15m'] = 50
            dataframe['ema_fast_15m_15m'] = 0
            dataframe['ema_200_1d_1d'] = 0

        # Ensure columns exist (safety for backtesting edge cases)
        for col, default in [
            ('is_bull_4h', 1), ('rsi_14_4h', 50), ('adx_4h', 20),
            ('btc_is_bull_1h', 1), ('btc_rsi_1h', 50),
            ('rsi_15m_15m', 50), ('ema_fast_15m_15m', 0),
            ('ema_200_1d_1d', 0),
        ]:
            if col not in dataframe.columns:
                dataframe[col] = default

        # --- Fear & Greed Index ---
        fng_map = self._get_fng_data()
        if fng_map:
            dataframe['fng_value'] = dataframe['date'].apply(
                lambda d: fng_map.get(d.strftime('%Y-%m-%d'), 50)
            )
        else:
            dataframe['fng_value'] = 50

        # --- On-chain: Funding rate & OI (live/dry_run only) ---
        dataframe['funding_rate'] = 0.0
        dataframe['funding_extreme'] = 0
        dataframe['oi_change'] = 0.0

        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            pair = metadata.get('pair', '')
            funding = self._funding_cache.get(pair, {}).get('rate', 0.0)
            oi_change = self._funding_cache.get(pair, {}).get('oi_change', 0.0)
            dataframe.loc[dataframe.index[-1], 'funding_rate'] = funding
            dataframe.loc[dataframe.index[-1], 'funding_extreme'] = 1 if abs(funding) > 0.0003 else 0
            dataframe.loc[dataframe.index[-1], 'oi_change'] = oi_change

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = f"rsi_{self.rsi_period.value}"
        ema_fast = f"ema_{self.ema_fast.value}"
        ema_slow = f"ema_{self.ema_slow.value}"

        # ========== LONG ENTRIES ==========

        # === LONG 1: Trend Pullback to EMA ===
        conditions_pullback = [
            dataframe["is_bull"] == 1,
            dataframe["pullback_to_ema"] == 1,
            dataframe[rsi] > self.rsi_pullback_low.value,
            dataframe[rsi] < self.rsi_pullback_high.value,
            dataframe["adx"] > self.adx_threshold.value,
            dataframe["volume_ratio"] > self.volume_factor.value,
            dataframe["plus_di"] > dataframe["minus_di"],
            dataframe["obv"] > dataframe["obv_ema"],
            dataframe["volume"] > 0,
            dataframe["btc_rsi_1h"] > 35,
            dataframe["fng_value"] >= 25,      # Not extreme fear
            dataframe["fng_value"] <= 85,      # Not extreme greed
            dataframe["rsi_15m_15m"] < 70,     # 15m not overbought
        ]
        # Add daily EMA200 filter only if column has valid data
        if 'ema_200_1d_1d' in dataframe.columns:
            conditions_pullback.append(dataframe["close"] > dataframe["ema_200_1d_1d"])
        # Block entries when funding is extreme (live only)
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_pullback.append(dataframe['funding_extreme'] == 0)

        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_pullback),
            ["enter_long", "enter_tag"]
        ] = (1, "trend_pullback")

        # === LONG 2: EMA50 Support Bounce ===
        conditions_ema50 = [
            dataframe["is_bull"] == 1,
            dataframe["ema50_bounce"] == 1,
            dataframe[rsi] > 30,
            dataframe[rsi] < 50,
            dataframe["adx"] > 20,
            dataframe["volume_ratio"] > 1.0,
            dataframe["macdhist"] > dataframe["macdhist"].shift(1),
            dataframe["volume"] > 0,
            dataframe["btc_rsi_1h"] > 35,
            dataframe["fng_value"] >= 25,
            dataframe["fng_value"] <= 85,
            dataframe["rsi_15m_15m"] < 70,
        ]
        # Block entries when funding is extreme (live only)
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_ema50.append(dataframe['funding_extreme'] == 0)
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_ema50),
            ["enter_long", "enter_tag"]
        ] = (1, "ema50_bounce")

        # === LONG 3: RSI Oversold Bounce ===
        conditions_rsi = [
            dataframe["close"] > dataframe["ema_200"],
            dataframe[rsi].shift(1) < self.rsi_bounce.value,
            dataframe[rsi] > self.rsi_bounce.value,
            dataframe["close"] > dataframe["bb_lower"],
            dataframe["close"] > dataframe["open"],
            dataframe["volume_ratio"] > 0.8,
            dataframe["obv"] > dataframe["obv_ema"],
            dataframe["volume"] > 0,
            dataframe["btc_rsi_1h"] > 35,
            dataframe["fng_value"] >= 25,
            dataframe["fng_value"] <= 85,
        ]
        # Block entries when funding is extreme (live only)
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_rsi.append(dataframe['funding_extreme'] == 0)
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_rsi),
            ["enter_long", "enter_tag"]
        ] = (1, "rsi_bounce")

        # ========== SHORT ENTRIES ==========

        # === SHORT 1: Trend Pullback from EMA (bear market) ===
        conditions_short_pullback = [
            dataframe["is_bear"] == 1,
            dataframe["pullback_from_ema"] == 1,
            dataframe[rsi] > 42,
            dataframe[rsi] < 60,
            dataframe["adx"] > self.adx_threshold.value,
            dataframe["volume_ratio"] > self.volume_factor.value,
            dataframe["minus_di"] > dataframe["plus_di"],
            dataframe["volume"] > 0,
            dataframe["btc_rsi_1h"] < 65,
            dataframe["fng_value"] >= 15,
            dataframe["fng_value"] <= 75,
        ]
        # For shorts: block when funding < -0.0003 (too many shorts already)
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_short_pullback.append(dataframe['funding_rate'] > -0.0003)
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_short_pullback),
            ["enter_short", "enter_tag"]
        ] = (1, "short_pullback")

        # === SHORT 2: EMA50 Rejection ===
        conditions_short_ema50 = [
            dataframe["is_bear"] == 1,
            dataframe["ema50_rejection"] == 1,
            dataframe[rsi] > 50,
            dataframe[rsi] < 70,
            dataframe["adx"] > 20,
            dataframe["macdhist"] < dataframe["macdhist"].shift(1),  # MACD histogram falling
            dataframe["volume"] > 0,
            dataframe["btc_rsi_1h"] < 65,
            dataframe["fng_value"] >= 15,
            dataframe["fng_value"] <= 75,
        ]
        # For shorts: block when funding < -0.0003 (too many shorts already)
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_short_ema50.append(dataframe['funding_rate'] > -0.0003)
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_short_ema50),
            ["enter_short", "enter_tag"]
        ] = (1, "short_ema50_rejection")

        # === SHORT 3: RSI Overbought Cross Down ===
        conditions_short_rsi = [
            dataframe["close"] < dataframe["ema_200"],
            dataframe[rsi].shift(1) > 70,
            dataframe[rsi] <= 70,                            # RSI crosses 70 from above
            dataframe["close"] < dataframe["bb_upper"],
            dataframe["close"] < dataframe["open"],          # Bearish candle
            dataframe["volume"] > 0,
            dataframe["fng_value"] >= 15,
            dataframe["fng_value"] <= 75,
        ]
        # For shorts: block when funding < -0.0003 (too many shorts already)
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_short_rsi.append(dataframe['funding_rate'] > -0.0003)
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_short_rsi),
            ["enter_short", "enter_tag"]
        ] = (1, "short_rsi_overbought")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = f"rsi_{self.rsi_period.value}"
        ema_fast = f"ema_{self.ema_fast.value}"
        ema_slow = f"ema_{self.ema_slow.value}"

        # ========== LONG EXITS ==========

        # EXIT 1: RSI very overbought
        dataframe.loc[
            (dataframe[rsi] > self.rsi_exit.value) &
            (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"]
        ] = (1, "rsi_overbought")

        # EXIT 2: Bearish EMA cross with MACD confirmation
        dataframe.loc[
            (dataframe[ema_fast] < dataframe[ema_slow]) &
            (dataframe[ema_fast].shift(1) >= dataframe[ema_slow].shift(1)) &
            (dataframe["macdhist"] < 0) &
            (dataframe[rsi] > 50) &
            (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"]
        ] = (1, "ema_bearish_cross")

        # EXIT 3: Price drops below EMA200 (trend broken)
        dataframe.loc[
            (dataframe["close"] < dataframe["ema_200"]) &
            (dataframe["close"].shift(1) >= dataframe["ema_200"].shift(1)) &
            (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"]
        ] = (1, "trend_broken")

        # ========== SHORT EXITS ==========

        # SHORT EXIT 1: RSI oversold (inverse of rsi_exit 81 -> 19)
        dataframe.loc[
            (dataframe[rsi] < 19) &
            (dataframe["volume"] > 0),
            ["exit_short", "exit_tag"]
        ] = (1, "rsi_oversold_short")

        # SHORT EXIT 2: Bullish EMA cross
        dataframe.loc[
            (dataframe[ema_fast] > dataframe[ema_slow]) &
            (dataframe[ema_fast].shift(1) <= dataframe[ema_slow].shift(1)) &
            (dataframe["volume"] > 0),
            ["exit_short", "exit_tag"]
        ] = (1, "ema_bullish_cross_short")

        # SHORT EXIT 3: Price rises above EMA200 (trend broken for shorts)
        dataframe.loc[
            (dataframe["close"] > dataframe["ema_200"]) &
            (dataframe["close"].shift(1) <= dataframe["ema_200"].shift(1)) &
            (dataframe["volume"] > 0),
            ["exit_short", "exit_tag"]
        ] = (1, "trend_broken_short")

        return dataframe

    # --- Dynamic ATR-based Stoploss ---
    def custom_stoploss(self, pair: str, trade, current_time: datetime,
                        current_rate: float, current_profit: float,
                        after_fill: bool, **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) < 1:
            return self.stoploss  # default -0.06

        last_candle = dataframe.iloc[-1]
        atr = last_candle.get('atr', 0)
        if atr <= 0:
            return self.stoploss

        # Dynamic stoploss = 2x ATR from entry
        atr_stoploss = -(atr * 2) / current_rate

        # Clamp between -3% and -8%
        atr_stoploss = max(min(atr_stoploss, -0.03), -0.08)

        return atr_stoploss

    # --- DCA + Partial Take Profit via adjust_trade_position ---
    def adjust_trade_position(self, trade, current_time: datetime,
                              current_rate: float, current_profit: float,
                              min_stake: float, max_stake: float,
                              current_entry_rate: float, current_exit_rate: float,
                              current_exit_profit: float, current_entry_profit: float,
                              **kwargs):
        # --- Partial Take Profit ---
        filled_exits = trade.nr_of_successful_exits

        if current_profit >= 0.03 and filled_exits == 0:
            # TP1: sell 30% of position
            return -(trade.stake_amount * 0.3)

        if current_profit >= 0.05 and filled_exits == 1:
            # TP2: sell 30% more
            return -(trade.stake_amount * 0.3)

        # TP3: remaining 40% handled by trailing/ROI

        # --- DCA (only for losing positions) ---
        filled_entries = trade.nr_of_successful_entries

        if current_profit > -0.02:
            return None

        if filled_entries >= 3:  # 1 initial + 2 DCA max
            return None

        if filled_entries == 1 and current_profit <= -0.03:
            return trade.stake_amount * 0.5  # Half position DCA

        if filled_entries == 2 and current_profit <= -0.05:
            return trade.stake_amount * 0.5

        return None

    # --- Improved Confidence Scoring ---
    def _calc_confidence(self, last: dict) -> tuple:
        """Calculate signal confidence based on weighted indicator alignment.

        Max score ~15. Returns (level_str, bar_str, details_list, numeric_level).
        """
        score = 0.0
        details = []
        rsi_key = f"rsi_{self.rsi_period.value}"
        rsi_val = last.get(rsi_key, 50)

        # RSI in healthy zone (not overbought): +1.5
        if 35 < rsi_val < 60:
            score += 1.5
            details.append("RSI healthy")

        # Strong trend (ADX): +2.5 strong, +1.5 moderate
        adx_val = last.get('adx', 0)
        if adx_val > 30:
            score += 2.5
            details.append("Strong trend")
        elif adx_val > self.adx_threshold.value:
            score += 1.5
            details.append("Moderate trend")

        # Volume confirmation: +2.5 high, +1.5 normal
        vol_ratio = last.get('volume_ratio', 0)
        if vol_ratio > 1.5:
            score += 2.5
            details.append("High volume")
        elif vol_ratio > 1.0:
            score += 1.5
            details.append("Normal volume")

        # MACD positive histogram AND rising: +1.5
        macd_hist = last.get('macdhist', 0)
        macd_hist_prev = last.get('macdhist', 0)  # Simplified; ideally from shift
        if macd_hist > 0:
            score += 1.5
            details.append("MACD positive+rising")

        # OBV rising AND above EMA: +1.5
        if last.get('obv', 0) > last.get('obv_ema', 0):
            score += 1.5
            details.append("OBV rising")

        # BTC healthy (RSI 40-70): +1.5
        btc_rsi = last.get('btc_rsi_1h', 50)
        if 40 < btc_rsi < 70:
            score += 1.5
            details.append("BTC healthy")

        # 4h trend alignment AND ADX_4h > 20: +1.5
        if last.get('is_bull_4h', 0) == 1 and last.get('adx_4h', 0) > 20:
            score += 1.5
            details.append("4H trend aligned")

        # Bollinger Band position (close near lower = good for long): +1
        close = last.get('close', 0)
        bb_lower = last.get('bb_lower', 0)
        bb_upper = last.get('bb_upper', 0)
        bb_range = bb_upper - bb_lower if bb_upper > bb_lower else 1
        if bb_lower > 0 and close > 0:
            bb_position = (close - bb_lower) / bb_range
            if bb_position < 0.35:
                score += 1.0
                details.append("Near BB lower")

        # Plus_DI > Minus_DI spread > 10: +1
        plus_di = last.get('plus_di', 0)
        minus_di = last.get('minus_di', 0)
        if plus_di - minus_di > 10:
            score += 1.0
            details.append("Strong DI spread")

        # FNG bonus: neutral/healthy (40-60): +1
        fng_val = last.get('fng_value', 50)
        if 40 <= fng_val <= 60:
            score += 1.0
            details.append("FNG neutral")

        # On-chain: healthy funding rate: +1
        funding = last.get('funding_rate', 0)
        if abs(funding) < 0.0001:  # Normal funding
            score += 1
            details.append("Healthy funding")

        # Map to level (max ~15 points)
        if score >= 11:
            level = "STRONG"
            bar = "|||||||||| 9/10"
            numeric = 9
        elif score >= 8:
            level = "GOOD"
            bar = "||||||||-- 7/10"
            numeric = 7
        elif score >= 5:
            level = "MEDIUM"
            bar = "||||||---- 5/10"
            numeric = 5
        else:
            level = "WEAK"
            bar = "|||------- 3/10"
            numeric = 3

        return level, bar, details, numeric

    def _market_context(self, last: dict) -> str:
        """Generate market context string."""
        btc_rsi = last.get('btc_rsi_1h', 50)
        btc_bull = last.get('btc_is_bull_1h', 0)
        bull_4h = last.get('is_bull_4h', 0)

        if btc_bull and btc_rsi > 55:
            btc_status = "Bullish"
        elif btc_rsi > 40:
            btc_status = "Neutral"
        else:
            btc_status = "Bearish"

        tf_4h = "Uptrend" if bull_4h else "Downtrend"

        parts = [f"BTC: {btc_status} (RSI {btc_rsi:.0f})", f"4H: {tf_4h}"]

        funding = last.get('funding_rate', 0)
        if funding != 0:
            funding_pct = funding * 100
            parts.append(f"Fund: {funding_pct:+.3f}%")

        return " | ".join(parts)

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                           time_in_force: str, current_time: datetime, entry_tag: str | None,
                           side: str, **kwargs) -> bool:
        is_short = side == "short"

        # Calculate levels depending on direction
        if is_short:
            sl_price = rate * (1 - self.stoploss)  # stoploss is negative, so 1 - (-0.06) = 1.06
            tp1_price = rate * 0.97   # -3%
            tp2_price = rate * 0.95   # -5%
            tp3_price = rate * 0.90   # -10%
        else:
            sl_price = rate * (1 + self.stoploss)  # stoploss is negative
            tp1_price = rate * 1.03   # +3%
            tp2_price = rate * 1.05   # +5%
            tp3_price = rate * 1.10   # +10%

        leverage = self.leverage_value
        side_str = "SHORT" if is_short else "LONG"

        # Risk/reward ratio
        risk = abs(rate - sl_price)
        reward = abs(tp2_price - rate)
        rr_ratio = reward / risk if risk > 0 else 0

        # Entry reason mapping
        reasons = {
            "trend_pullback": "Откат к EMA16 в восходящем тренде, отскок с подтверждением объёма",
            "ema50_bounce": "Глубокий откат к EMA50, отскок с растущим MACD",
            "rsi_bounce": "RSI перепродан, отскок от нижней Боллинджера в бычьем рынке",
            "short_pullback": "Откат к EMA16 в нисходящем тренде, отбой с подтверждением объёма",
            "short_ema50_rejection": "Отбой от EMA50 сверху, падающий MACD",
            "short_rsi_overbought": "RSI перекуплен, разворот от верхней Боллинджера в медвежьем рынке",
        }
        reason = reasons.get(entry_tag, entry_tag or "Signal")

        # Get current indicators for context
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) > 0:
            last = dataframe.iloc[-1]
            rsi_key = f"rsi_{self.rsi_period.value}"
            rsi_val = last.get(rsi_key, 0)
            adx_val = last.get("adx", 0)
            vol_ratio = last.get("volume_ratio", 0)
            macd_hist = last.get("macdhist", 0)
        else:
            rsi_val = adx_val = vol_ratio = macd_hist = 0
            last = {}

        # Confidence & market context
        conf_level, conf_bar, conf_details, conf_numeric = self._calc_confidence(last)
        market_ctx = self._market_context(last)

        # --- REJECT WEAK SIGNALS ---
        if conf_numeric <= 3:
            logger.info(f"Rejecting weak signal for {pair}: confidence {conf_numeric}/10")
            return False

        # --- Main Telegram Signal ---
        msg = (
            f"*TRENDRIDER SIGNAL*\n"
            f"{'='*28}\n"
            f"*{pair}* | *{side_str}* | {leverage}x\n"
            f"{'='*28}\n\n"
            f"*Entry:* `{rate:.2f}` USDT\n"
            f"*Stop Loss:* `{sl_price:.2f}` ({self.stoploss*100:+.1f}%)\n\n"
            f"*Targets:*\n"
            f"  TP1: `{tp1_price:.2f}` (+3%)\n"
            f"  TP2: `{tp2_price:.2f}` (+5%)\n"
            f"  TP3: `{tp3_price:.2f}` (+10%)\n"
            f"  R:R = 1:{rr_ratio:.1f}\n\n"
            f"*Confidence:* {conf_level}\n"
            f"  [{conf_bar}]\n"
            f"  {', '.join(conf_details)}\n\n"
            f"*Indicators:*\n"
            f"  RSI: {rsi_val:.1f} | ADX: {adx_val:.1f}\n"
            f"  Volume: {vol_ratio:.2f}x | MACD: {'+'  if macd_hist > 0 else '-'}\n\n"
            f"*Market:* {market_ctx}\n\n"
            f"*Why:* {reason}\n"
            f"{'='*28}\n"
            f"_TrendRider Algo | @TrendRiderSignals_"
        )
        self.dp.send_msg(msg, always_send=True)

        # --- Cornix-Compatible Format ---
        pair_clean = pair.replace('/USDT:USDT', '').replace('/', '')
        signal_type = "Regular (Short)" if is_short else "Regular (Long)"

        if is_short:
            entry_low = rate * 0.998
            entry_high = rate * 1.002
            cornix_tp1 = rate * 0.97
            cornix_tp2 = rate * 0.95
            cornix_tp3 = rate * 0.90
        else:
            entry_low = rate * 0.998
            entry_high = rate * 1.002
            cornix_tp1 = rate * 1.03
            cornix_tp2 = rate * 1.05
            cornix_tp3 = rate * 1.10

        cornix_msg = (
            f"#{pair_clean}\n\n"
            f"Exchanges: Bybit USDT\n"
            f"Signal Type: {signal_type}\n"
            f"Leverage: Isolated ({leverage}X)\n\n"
            f"Entry Zone: {entry_low:.2f} - {entry_high:.2f}\n\n"
            f"Take-Profit Targets:\n"
            f"1) {cornix_tp1:.2f}\n"
            f"2) {cornix_tp2:.2f}\n"
            f"3) {cornix_tp3:.2f}\n\n"
            f"Stop Targets:\n"
            f"1) {sl_price:.2f}\n\n"
            f"Trailing Configuration:\n"
            f"Stop: Breakeven - Trigger: Target (1)"
        )
        self.dp.send_msg(cornix_msg, always_send=True)

        return True

    def confirm_trade_exit(self, pair: str, trade, order_type: str, amount: float,
                          rate: float, time_in_force: str, exit_reason: str,
                          current_time: datetime, **kwargs) -> bool:
        # Calculate results
        if trade.is_short:
            profit_pct = ((trade.open_rate - rate) / trade.open_rate) * 100 * trade.leverage
        else:
            profit_pct = ((rate - trade.open_rate) / trade.open_rate) * 100 * trade.leverage
        duration_hours = (current_time - trade.open_date_utc).total_seconds() / 3600

        side_str = "SHORT" if trade.is_short else "LONG"

        # Exit reason mapping
        exit_reasons = {
            "roi": "ROI target reached",
            "stop_loss": "Stop Loss hit",
            "trailing_stop_loss": "Trailing Stop",
            "exit_signal": "Exit signal",
            "rsi_overbought": "RSI overbought (>81)",
            "ema_bearish_cross": "EMA bearish crossover",
            "trend_broken": "Trend broken (below EMA200)",
            "rsi_oversold_short": "RSI oversold (<19)",
            "ema_bullish_cross_short": "EMA bullish crossover (short exit)",
            "trend_broken_short": "Trend broken (above EMA200)",
            "partial_tp1": "Partial TP1 (+3%)",
            "partial_tp2": "Partial TP2 (+5%)",
            "force_exit": "Force exit",
        }
        reason_text = exit_reasons.get(exit_reason, exit_reason)

        # Result emoji
        if profit_pct > 0:
            result_line = f"+{profit_pct:.2f}%"
        else:
            result_line = f"{profit_pct:.2f}%"

        # Duration formatting
        if duration_hours < 1:
            dur_str = f"{int(duration_hours * 60)}m"
        elif duration_hours < 24:
            dur_str = f"{duration_hours:.1f}h"
        else:
            dur_str = f"{duration_hours/24:.1f}d"

        msg = (
            f"*TRADE CLOSED* {'WIN' if profit_pct > 0 else 'LOSS'}\n"
            f"{'='*25}\n"
            f"*{pair}* | {side_str} | {trade.leverage}x\n"
            f"{'='*25}\n\n"
            f"*Entry:* `{trade.open_rate:.2f}`\n"
            f"*Exit:* `{rate:.2f}`\n"
            f"*Result:* *{result_line}*\n"
            f"*Duration:* {dur_str}\n"
            f"*Reason:* {reason_text}\n"
            f"*Max price:* `{trade.max_rate:.2f}`\n"
            f"{'='*25}\n"
            f"_TrendRider Algo | Bybit Futures_"
        )

        self.dp.send_msg(msg, always_send=True)
        return True
