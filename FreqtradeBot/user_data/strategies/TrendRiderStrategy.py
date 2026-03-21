"""
TrendRiderStrategy — "Trend Rider"

Philosophy: Ride established uptrends with WIDE stoploss.
Key insight: crypto swings 2-4% per hour. Stoploss must be >= 5-6%.

Lessons from v1-v5:
- v4 bull backtest: -9.74% (28 trades, 6 min avg, trailing too tight)
- v6.0 bull backtest: -72.76% (369 trades, 2 min avg, stoploss too tight)
- Problem: 1.5x ATR ~ 1.5% stoploss, but BTC swings 2-3%/hour
- Solution: 3x ATR stoploss (~4-6%), NO custom stoploss, let ROI+trailing work

Rules:
- LONG only (shorts failed in v5)
- Bear market = no trading
- WIDE stoploss (6%) to survive normal volatility
- WIDE trailing (2% trail after 2.5% profit)
- FEW high-quality entries (quality > quantity)
"""

import talib.abstract as ta
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
from functools import reduce


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
    stoploss = -0.06           # 6% (was 4% in v4 — too tight!)
    use_custom_stoploss = False # DISABLED — custom stoploss was the killer

    # --- Trailing Stop: WIDE ---
    trailing_stop = True
    trailing_stop_positive = 0.02        # 2% trail (fix #3: was 3%)
    trailing_stop_positive_offset = 0.025 # Activate after +2.5% (fix #2: was 5%)
    trailing_only_offset_is_reached = True

    # --- General ---
    timeframe = "1h"
    startup_candle_count = 210
    process_only_new_candles = True
    can_short = False

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

    def leverage(self, pair: str, current_time, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str,
                 side: str, **kwargs) -> float:
        return min(float(self.leverage_value), max_leverage)

    def informative_pairs(self):
        return []

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

        # Regime
        dataframe["is_bull"] = (
            (dataframe["close"] > dataframe["ema_200"]) &
            (dataframe["ema_50"] > dataframe["ema_200"])
        ).astype(int)

        dataframe["is_bear"] = (
            (dataframe["close"] < dataframe["ema_200"]) &
            (dataframe["ema_50"] < dataframe["ema_200"])
        ).astype(int)

        # Pullback detection: price dipped to EMA support and bouncing
        ema_slow_key = f"ema_{self.ema_slow.value}"
        if ema_slow_key in dataframe.columns:
            dataframe["pullback_to_ema"] = (
                (dataframe["low"] <= dataframe[ema_slow_key] * 1.01) &
                (dataframe["close"] > dataframe[ema_slow_key]) &
                (dataframe["close"] > dataframe["open"])  # Bullish candle
            ).astype(int)
        else:
            dataframe["pullback_to_ema"] = 0

        # EMA50 support bounce
        dataframe["ema50_bounce"] = (
            (dataframe["low"] <= dataframe["ema_50"] * 1.01) &
            (dataframe["close"] > dataframe["ema_50"]) &
            (dataframe["close"] > dataframe["open"])
        ).astype(int)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = f"rsi_{self.rsi_period.value}"
        ema_fast = f"ema_{self.ema_fast.value}"
        ema_slow = f"ema_{self.ema_slow.value}"

        # === LONG 1: Trend Pullback to EMA ===
        # Price pulls back to EMA21 support in strong uptrend, then bounces
        conditions_pullback = [
            dataframe["is_bull"] == 1,
            dataframe["is_bear"] == 0,                            # fix #1: block bear entries
            dataframe["pullback_to_ema"] == 1,
            dataframe[rsi] > self.rsi_pullback_low.value,
            dataframe[rsi] < self.rsi_pullback_high.value,
            dataframe["adx"] > self.adx_threshold.value,
            dataframe["volume_ratio"] > self.volume_factor.value,
            dataframe["plus_di"] > dataframe["minus_di"],         # Bullish DI
            dataframe["obv"] > dataframe["obv_ema"],
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_pullback),
            ["enter_long", "enter_tag"]
        ] = (1, "trend_pullback")

        # === LONG 2: EMA50 Support Bounce ===
        # Deeper pullback to EMA50 in uptrend — stronger support
        conditions_ema50 = [
            dataframe["enter_long"] == 0,                          # fix #11: don't overwrite
            dataframe["is_bull"] == 1,
            dataframe["is_bear"] == 0,                             # fix #1: block bear entries
            dataframe["ema50_bounce"] == 1,
            dataframe[rsi] > 30,
            dataframe[rsi] < 50,
            dataframe["adx"] > 20,
            dataframe["volume_ratio"] > 1.0,
            # fix #7: 2-candle MACD confirmation
            (dataframe["macdhist"] > dataframe["macdhist"].shift(1)) &
            (dataframe["macdhist"].shift(1) > dataframe["macdhist"].shift(2)),
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_ema50),
            ["enter_long", "enter_tag"]
        ] = (1, "ema50_bounce")

        # === LONG 3: RSI Oversold Bounce ===
        # RSI crosses 30 from below in bull/neutral market
        conditions_rsi = [
            dataframe["enter_long"] == 0,                          # fix #11: don't overwrite
            dataframe["is_bear"] == 0,                             # fix #1: block bear entries
            dataframe["close"] > dataframe["ema_200"],
            dataframe[rsi].shift(1) < self.rsi_bounce.value,
            dataframe[rsi] > self.rsi_bounce.value,
            dataframe["close"] > dataframe["bb_lower"],
            dataframe["close"] > dataframe["open"],                # Bullish candle
            dataframe["volume_ratio"] > 0.8,
            dataframe["obv"] > dataframe["obv_ema"],
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_rsi),
            ["enter_long", "enter_tag"]
        ] = (1, "rsi_bounce")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = f"rsi_{self.rsi_period.value}"
        ema_fast = f"ema_{self.ema_fast.value}"
        ema_slow = f"ema_{self.ema_slow.value}"

        # EXIT 1: RSI very overbought (fix #10: only during bull)
        dataframe.loc[
            (dataframe["is_bull"] == 1) &
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

        return dataframe
