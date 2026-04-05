"""
TrendRiderStrategy — "Trend Rider" v2.0

Philosophy: Ride established trends with WIDE stoploss.
Key insight: crypto swings 2-4% per hour. Stoploss must be >= 5-6%.

v2.0 additions:
- Improved confidence scoring with weighted factors
- Cornix-compatible signal format
- Reject weak signals (confidence < 5)
- Multi-timeframe 15m + Daily confirmation
- Fear & Greed Index integration
- Persistent price alerts (SQLite)

Modular architecture: config, database, on-chain, confidence, messaging
are extracted into separate modules (trendrider_*.py).
"""

import talib.abstract as ta
from datetime import datetime
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, merge_informative_pair
from pandas import DataFrame
from functools import reduce
import logging

from trendrider_config import (
    SETUP_NAMES, ALERT_COOLDOWN_SECONDS, EMA_PROXIMITY_PCT,
    ENTRY_ZONE_PCT, TP1_PCT, TP2_PCT, TP3_PCT,
    CONFIDENCE_MIN_DEFAULT, CONFIDENCE_MIN_BEAR,
    FNG_HEALTHY_MIN, FNG_HEALTHY_MAX,
    BTC_RSI_LONG_MIN,
)
# Note: TP1/TP2/TP3 are still used for R:R ratio calculation and signal queue,
# but are no longer displayed in Telegram messages (DCA/partial TP disabled).
from trendrider_database import AlertsDB
from trendrider_onchain import FearGreedFetcher, OnChainDataFetcher
from trendrider_confidence import calc_confidence, market_context, get_market_regime, get_estimated_hold
from trendrider_messaging import (
    build_detailed_reason, format_entry_signal, format_cornix_signal,
    format_exit_report, format_exit_footer, format_price_alert, get_running_stats,
)

logger = logging.getLogger(__name__)


class TrendRiderStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # --- ROI: Wide, let winners run ---
    minimal_roi = {
        "0": 0.30,      # 30% immediate (widened for better R:R)
        "124": 0.136,   # 13.6% after ~2h
        "290": 0.06,    # 6% after ~5h (widened for better R:R)
        "764": 0,       # breakeven after ~12.7h
    }

    # --- Stoploss: WIDE for crypto volatility ---
    stoploss = -0.035          # V3: tightened from -0.05 for defensive cut (backtest: MaxDD 4.08%→1.12%)
    use_custom_stoploss = False

    # --- Trailing Stop: WIDE ---
    trailing_stop = True
    trailing_stop_positive = 0.03        # 3% trail
    trailing_stop_positive_offset = 0.05 # Activate after +5%
    trailing_only_offset_is_reached = True

    # --- General ---
    timeframe = "1h"
    startup_candle_count = 210
    process_only_new_candles = True
    can_short = False
    position_adjustment_enable = False

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
        "rsi_pullback_low": 25,
        "rsi_pullback_high": 70,
        "rsi_bounce": 35,
        "adx_threshold": 15,
        "volume_factor": 0.7,
    }

    sell_params = {
        "rsi_exit": 82,
    }

    # --- HyperOpt Parameters ---
    ema_fast = IntParameter(5, 15, default=9, space="buy")
    ema_slow = IntParameter(15, 30, default=21, space="buy")
    rsi_period = IntParameter(10, 20, default=14, space="buy")
    rsi_pullback_low = IntParameter(25, 48, default=40, space="buy")
    rsi_pullback_high = IntParameter(52, 70, default=58, space="buy")
    rsi_bounce = IntParameter(25, 35, default=30, space="buy")
    rsi_exit = IntParameter(72, 85, default=78, space="sell")
    adx_threshold = IntParameter(15, 35, default=25, space="buy")
    volume_factor = DecimalParameter(1.0, 2.5, default=1.3, space="buy")

    # --- Leverage: fixed 3x (adaptive tested, worse results) ---
    leverage_value = 3

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._db = AlertsDB(config)
        self._fng_fetcher = FearGreedFetcher(config)
        self._onchain = OnChainDataFetcher()

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
                    self._onchain.fetch_funding_rate(pair)
                    self._onchain.fetch_open_interest(pair)
                except Exception as e:
                    logger.warning(f"On-chain data fetch failed for {pair}: {e}")

        for pair in self.dp.current_whitelist():
            # Cooldown: max 1 alert per pair per 4 hours (persistent via SQLite)
            last_alert = self._db.get_last_alert(pair)
            if last_alert and (current_time - last_alert).total_seconds() < ALERT_COOLDOWN_SECONDS:
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

            # Check proximity to EMA support
            dist_ema = (close - ema_slow_val) / ema_slow_val * 100
            dist_ema50 = (close - ema_50_val) / ema_50_val * 100 if ema_50_val > 0 else 999

            zone = None
            zone_price = 0
            zone_name = ""

            if 0 < dist_ema < EMA_PROXIMITY_PCT:
                zone = "ema_slow"
                zone_price = ema_slow_val
                zone_name = f"EMA{self.ema_slow.value}"
            elif 0 < dist_ema50 < EMA_PROXIMITY_PCT:
                zone = "ema50"
                zone_price = ema_50_val
                zone_name = "EMA50"

            if zone:
                rsi_key = f"rsi_{self.rsi_period.value}"
                rsi_val = last.get(rsi_key, 50)
                adx_val = last.get('adx', 0)
                vol_ratio = last.get('volume_ratio', 0)

                dist = (close - zone_price) / zone_price * 100

                msg = format_price_alert(pair, close, zone_name, zone_price, dist,
                                         rsi_val, adx_val, vol_ratio)
                self.dp.send_msg(msg, always_send=True)
                self._db.set_last_alert(pair, current_time)

    def informative_pairs(self):
        pairs = self.dp.current_whitelist() if self.dp else []
        informative = []
        for pair in pairs:
            informative.append((pair, "4h"))

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
        dataframe["macdhist_prev"] = macd["macdhist"].shift(1)

        # Bollinger Bands
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bb["upperband"]
        dataframe["bb_middle"] = bb["middleband"]
        dataframe["bb_lower"] = bb["lowerband"]
        # BB width for volatility regime (Phase 8.5)
        dataframe["bb_width"] = (dataframe["bb_upper"] - dataframe["bb_lower"]) / (dataframe["bb_middle"] + 1e-10)
        dataframe["bb_width_sma"] = ta.SMA(dataframe["bb_width"], timeperiod=50)

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
                (dataframe["low"] <= dataframe[ema_slow_key] * 1.02) &
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

            # Daily data for macro trend
            df_1d = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe='1d')
            if len(df_1d) > 0:
                df_1d['ema_200'] = ta.EMA(df_1d, timeperiod=200)
                dataframe = merge_informative_pair(
                    dataframe,
                    df_1d[['date', 'ema_200']],
                    self.timeframe, '1d', ffill=True
                )
            else:
                dataframe['ema_200_1d'] = 0

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
            dataframe['ema_200_1d'] = 0

        # Ensure columns exist (safety for backtesting edge cases)
        for col, default in [
            ('is_bull_4h', 1), ('rsi_14_4h', 50), ('adx_4h', 20),
            ('btc_is_bull_1h', 1), ('btc_rsi_1h', 50),

            ('ema_200_1d', 0),
        ]:
            if col not in dataframe.columns:
                dataframe[col] = default

        # --- Fear & Greed Index ---
        fng_map = self._fng_fetcher.fetch()
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
            funding = self._onchain.cache.get(pair, {}).get('rate', 0.0)
            oi_change = self._onchain.cache.get(pair, {}).get('oi_change', 0.0)
            dataframe.loc[dataframe.index[-1], 'funding_rate'] = funding
            dataframe.loc[dataframe.index[-1], 'funding_extreme'] = 1 if abs(funding) > 0.0003 else 0
            dataframe.loc[dataframe.index[-1], 'oi_change'] = oi_change

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = f"rsi_{self.rsi_period.value}"

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
            dataframe["btc_rsi_1h"] > BTC_RSI_LONG_MIN,
            dataframe["fng_value"] >= FNG_HEALTHY_MIN,      # Not extreme fear
            dataframe["fng_value"] <= FNG_HEALTHY_MAX,      # Not extreme greed
            dataframe[rsi] < 70,                 # Not overbought
        ]
        # Daily EMA200 filter — helps filter bad entries
        if 'ema_200_1d' in dataframe.columns:
            conditions_pullback.append(dataframe["close"] > dataframe["ema_200_1d"])
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
            dataframe["btc_rsi_1h"] > BTC_RSI_LONG_MIN,
            dataframe["fng_value"] >= FNG_HEALTHY_MIN,
            dataframe["fng_value"] <= FNG_HEALTHY_MAX,
            dataframe[rsi] < 70,
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
            dataframe["btc_rsi_1h"] > BTC_RSI_LONG_MIN,
            dataframe["fng_value"] >= FNG_HEALTHY_MIN,
            dataframe["fng_value"] <= FNG_HEALTHY_MAX,
        ]
        # Block entries when funding is extreme (live only)
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_rsi.append(dataframe['funding_extreme'] == 0)
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_rsi),
            ["enter_long", "enter_tag"]
        ] = (1, "rsi_bounce")

        # === LONG 4: EMA Crossover — DISABLED (0% win rate in March 2026 backtest, 4 trades all losses) ===
        # ema_fast_key = f"ema_{self.ema_fast.value}"
        # ema_slow_key = f"ema_{self.ema_slow.value}"
        # conditions_ema_cross = [
        #     (dataframe[ema_fast_key] > dataframe[ema_slow_key]) &
        #     (dataframe[ema_fast_key].shift(1) <= dataframe[ema_slow_key].shift(1)),
        #     dataframe[rsi] > 40,
        #     dataframe[rsi] < 75,
        #     dataframe["close"] > dataframe["ema_200"],
        #     dataframe["volume_ratio"] > 0.5,
        #     dataframe["volume"] > 0,
        #     dataframe["btc_rsi_1h"] > BTC_RSI_LONG_MIN,
        #     dataframe["fng_value"] >= FNG_HEALTHY_MIN,
        #     dataframe["fng_value"] <= FNG_HEALTHY_MAX,
        # ]
        # if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
        #     conditions_ema_cross.append(dataframe['funding_extreme'] == 0)
        # dataframe.loc[
        #     reduce(lambda x, y: x & y, conditions_ema_cross),
        #     ["enter_long", "enter_tag"]
        # ] = (1, "ema_crossover")

        # === LONG 5: Bollinger Band Bounce (loosened: RSI<45, vol>0.3x, within 0.5% of BB lower) ===
        conditions_bb = [
            dataframe["close"] <= dataframe["bb_lower"] * 1.005,           # close within 0.5% of BB lower
            dataframe["close"] > dataframe["open"],                         # bullish candle (bounce)
            dataframe[rsi] < 40,                                           # loosened from 35 to generate more trades
            dataframe["volume_ratio"] > 0.3,
            dataframe["volume"] > 0,
            dataframe["btc_rsi_1h"] > BTC_RSI_LONG_MIN,
            dataframe["fng_value"] >= FNG_HEALTHY_MIN,
            dataframe["fng_value"] <= FNG_HEALTHY_MAX,
        ]
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_bb.append(dataframe['funding_extreme'] == 0)
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_bb),
            ["enter_long", "enter_tag"]
        ] = (1, "bb_bounce")

        # === LONG 6: MACD Histogram Reversal (tightened: RSI 40-60, EMA200 filter, volume 0.8x) ===
        conditions_macd = [
            (dataframe["macdhist"] > 0) &
            (dataframe["macdhist"].shift(1) <= 0),  # histogram crossed above zero
            dataframe["close"] > dataframe["ema_50"],
            dataframe["close"] > dataframe["ema_200"],  # confirm uptrend
            dataframe[rsi] > 45,
            dataframe[rsi] < 60,
            dataframe["adx"] > 20,
            dataframe["is_bull_4h"] == 1,
            dataframe["volume_ratio"] > 0.8,            # volume confirmation
            dataframe["volume"] > 0,
            dataframe["btc_rsi_1h"] > BTC_RSI_LONG_MIN,
            dataframe["fng_value"] >= FNG_HEALTHY_MIN,
            dataframe["fng_value"] <= FNG_HEALTHY_MAX,
        ]
        if self.dp and self.dp.runmode.value in ('live', 'dry_run'):
            conditions_macd.append(dataframe['funding_extreme'] == 0)
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_macd),
            ["enter_long", "enter_tag"]
        ] = (1, "macd_reversal")

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

        # EXIT 3: Price drops 3%+ below EMA200 for 2 consecutive candles (V3: was 1% single-candle, too noisy)
        dataframe.loc[
            (dataframe["close"] < dataframe["ema_200"] * 0.97) &
            (dataframe["close"].shift(1) < dataframe["ema_200"].shift(1) * 0.97) &
            (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"]
        ] = (1, "trend_broken")

        return dataframe

    def custom_exit(self, pair: str, trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """Time-based exits: V3 adds early loss cut (4h/-3%) before 24h timeout."""
        duration_hours = (current_time - trade.open_date_utc).total_seconds() / 3600
        if duration_hours >= 4 and current_profit < -0.03:
            return "early_loss_cut"
        if duration_hours >= 24 and current_profit < 0.01:
            return "time_exit_24h"
        return None

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                           time_in_force: str, current_time: datetime, entry_tag: str | None,
                           side: str, **kwargs) -> bool:
        # Calculate levels (LONG only, can_short = False)
        sl_price = rate * (1 + self.stoploss)
        tp1_price = rate * (1 + TP1_PCT)
        tp2_price = rate * (1 + TP2_PCT)
        tp3_price = rate * (1 + TP3_PCT)

        leverage = self.leverage_value
        side_str = "LONG"

        risk = abs(rate - sl_price)
        reward = abs(tp2_price - rate)
        rr_ratio = reward / risk if risk > 0 else 0

        # Get indicators
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

        # Use modules
        reason = build_detailed_reason(entry_tag, last, rate, self.ema_fast.value, self.ema_slow.value, self.rsi_period.value)
        setup_name = SETUP_NAMES.get(entry_tag, "Signal")
        conf_level, conf_bar, conf_details, conf_numeric = calc_confidence(last, self.adx_threshold.value, self.rsi_period.value)
        market_ctx = market_context(last)
        regime = get_market_regime(last)

        # Portfolio heat
        open_trades = 0
        max_trades = self.config.get('max_open_trades', 4)
        try:
            from freqtrade.persistence import Trade
            open_trades = Trade.get_count_open_trades()
        except Exception:
            pass
        heat_str = f"{open_trades}/{max_trades} positions open"

        est_hold = get_estimated_hold(conf_numeric)

        # Invalidation
        ema_200 = last.get('ema_200', 0)
        bb_lower = last.get('bb_lower', 0)
        invalidation = max(ema_200, bb_lower) if ema_200 > 0 else sl_price
        inv_label = "EMA200" if invalidation == ema_200 else "BB Lower"

        # Reject weak signals
        min_conf = CONFIDENCE_MIN_BEAR if "Bear" in regime else CONFIDENCE_MIN_DEFAULT
        if conf_numeric < min_conf:
            logger.info(f"Rejecting signal for {pair}: confidence {conf_numeric}/10 < {min_conf} (regime: {regime})")
            return False

        # Signal number
        signal_num = self._db.next_signal_number()

        # Send main signal
        msg = format_entry_signal(
            signal_num, pair, side_str, leverage, setup_name, rate,
            sl_price, self.stoploss, rr_ratio,
            conf_level, conf_numeric, conf_bar, conf_details,
            regime, heat_str, est_hold, invalidation, inv_label,
            rsi_val, adx_val, vol_ratio, macd_hist, market_ctx, reason
        )
        self.dp.send_msg(msg, always_send=True)

        # Send Cornix signal
        cornix_msg = format_cornix_signal(pair, side_str, leverage, rate, sl_price,
                                         tp1_price, tp2_price, tp3_price)
        self.dp.send_msg(cornix_msg, always_send=True)

        # Queue for free channel
        entry_low = rate * (1 - ENTRY_ZONE_PCT)
        entry_high = rate * (1 + ENTRY_ZONE_PCT)
        self._db.queue_signal(
            signal_num, pair, side_str, leverage, setup_name,
            entry_low, entry_high, sl_price, self.stoploss * 100,
            tp1_price, tp2_price, tp3_price, rr_ratio, regime
        )

        return True

    def confirm_trade_exit(self, pair: str, trade, order_type: str, amount: float,
                          rate: float, time_in_force: str, exit_reason: str,
                          current_time: datetime, **kwargs) -> bool:
        msg = format_exit_report(pair, trade, rate, exit_reason, current_time)
        stats_line = get_running_stats()
        msg += format_exit_footer(stats_line)
        self.dp.send_msg(msg, always_send=True)
        return True
