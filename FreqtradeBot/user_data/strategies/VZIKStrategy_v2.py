"""
VZIK Crypto Strategy v2.0
Optimized based on backtest v1.0 results:
- Longs are profitable, shorts lose money → stricter short filters
- RSI bounce is the best signal → enhanced
- Reduced stoploss, better trailing
- Added ADX trend filter
"""

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta


class VZIKStrategy_v2(IStrategy):

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = True

    # Tighter ROI — take profits faster
    minimal_roi = {
        "0": 0.05,     # 5% immediately
        "30": 0.035,   # 3.5% after 30min
        "60": 0.025,   # 2.5% after 1h
        "120": 0.02,   # 2% after 2h
        "240": 0.015,  # 1.5% after 4h
        "480": 0.01,   # 1% after 8h
    }

    # Tighter stoploss (was -4%, now -3%)
    stoploss = -0.03

    # Better trailing
    trailing_stop = True
    trailing_stop_positive = 0.01    # activate at +1%
    trailing_stop_positive_offset = 0.02  # start trailing at +2%
    trailing_only_offset_is_reached = True

    startup_candle_count = 50

    order_time_in_force = {
        "entry": "GTC",
        "exit": "GTC",
    }

    # Lower leverage for shorts (they lose more)
    leverage_long = 3
    leverage_short = 2

    # === Hyperopt parameters ===
    ema_fast = IntParameter(5, 15, default=9, space="buy", optimize=True)
    ema_slow = IntParameter(15, 30, default=21, space="buy", optimize=True)
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=True)
    rsi_buy = IntParameter(25, 40, default=30, space="buy", optimize=True)
    rsi_sell = IntParameter(60, 80, default=70, space="sell", optimize=True)
    volume_factor = DecimalParameter(1.0, 3.0, default=1.5, decimals=1, space="buy", optimize=True)

    # ADX filter — only trade when trend is strong
    adx_threshold = IntParameter(15, 35, default=20, space="buy", optimize=True)

    def leverage(self, pair: str, current_time, current_rate: float,
                 proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        if side == "short":
            return min(self.leverage_short, max_leverage)
        return min(self.leverage_long, max_leverage)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # === EMA ===
        for period in range(5, 31):
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)

        # === RSI ===
        for period in range(10, 21):
            dataframe[f"rsi_{period}"] = ta.RSI(dataframe, timeperiod=period)

        # === ADX (trend strength) ===
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)

        # === OBV ===
        dataframe["obv"] = ta.OBV(dataframe)
        dataframe["obv_ema"] = ta.EMA(dataframe["obv"], timeperiod=20)
        dataframe["obv_slope"] = dataframe["obv"].diff(3)

        # === ATR ===
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        # === Volume EMA ===
        dataframe["volume_ema"] = ta.EMA(dataframe["volume"], timeperiod=20)

        # === MACD ===
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # === Bollinger Bands ===
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_lower"] = bollinger["lowerband"]
        dataframe["bb_mid"] = bollinger["middleband"]

        # === Stochastic RSI ===
        stoch = ta.STOCHRSI(dataframe, timeperiod=14, fastk_period=3, fastd_period=3)
        dataframe["stochrsi_k"] = stoch["fastk"]
        dataframe["stochrsi_d"] = stoch["fastd"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast_col = f"ema_{self.ema_fast.value}"
        ema_slow_col = f"ema_{self.ema_slow.value}"
        rsi_col = f"rsi_{self.rsi_period.value}"

        # === LONG: EMA crossover + ADX + volume ===
        conditions_long = [
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) <= dataframe[ema_slow_col].shift(1)),
            (dataframe[rsi_col] > self.rsi_buy.value),
            (dataframe[rsi_col] < self.rsi_sell.value),
            (dataframe["adx"] > self.adx_threshold.value),
            (dataframe["plus_di"] > dataframe["minus_di"]),  # uptrend confirmed by DI
            (dataframe["volume"] > dataframe["volume_ema"] * self.volume_factor.value),
            (dataframe["obv_slope"] > 0),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_cross_long")

        # === LONG: RSI bounce (best signal from v1!) ===
        conditions_rsi_long = [
            (dataframe[rsi_col].shift(1) < 30),
            (dataframe[rsi_col] > 30),
            (dataframe["close"] > dataframe["bb_lower"]),
            (dataframe["obv_slope"] > 0),
            (dataframe["adx"] > 15),  # at least some trend
            (dataframe["stochrsi_k"] > dataframe["stochrsi_d"]),  # stoch RSI confirming
            (dataframe["volume"] > dataframe["volume_ema"] * 0.8),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_rsi_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi_bounce_long")

        # === SHORT: much stricter filters (shorts were losing) ===
        conditions_short = [
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) >= dataframe[ema_slow_col].shift(1)),
            (dataframe[rsi_col] > 50),  # only short from upper RSI (was 35)
            (dataframe[rsi_col] < self.rsi_sell.value),
            (dataframe["adx"] > 25),  # need STRONG trend for shorts (was 20)
            (dataframe["minus_di"] > dataframe["plus_di"]),  # downtrend confirmed
            (dataframe["volume"] > dataframe["volume_ema"] * 1.5),  # higher volume bar
            (dataframe["obv_slope"] < 0),
            (dataframe["macdhist"] < 0),
            (dataframe["macdhist"].shift(1) < dataframe["macdhist"].shift(2)),  # MACD declining
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_short, axis=0), index=dataframe.index),
            ["enter_short", "enter_tag"],
        ] = (1, "ema_cross_short")

        # === SHORT: RSI rejection (also strict) ===
        conditions_rsi_short = [
            (dataframe[rsi_col].shift(1) > 75),  # was 70, now stricter
            (dataframe[rsi_col] < 75),
            (dataframe["close"] < dataframe["bb_upper"]),
            (dataframe["obv_slope"] < 0),
            (dataframe["adx"] > 25),  # strong trend needed
            (dataframe["minus_di"] > dataframe["plus_di"]),  # downtrend confirmed
            (dataframe["volume"] > dataframe["volume_ema"] * 1.2),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_rsi_short, axis=0), index=dataframe.index),
            ["enter_short", "enter_tag"],
        ] = (1, "rsi_reject_short")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast_col = f"ema_{self.ema_fast.value}"
        ema_slow_col = f"ema_{self.ema_slow.value}"
        rsi_col = f"rsi_{self.rsi_period.value}"

        # === Exit LONG: EMA cross down OR RSI overbought ===
        conditions_exit_long = [
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[rsi_col] > 60),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_exit_long, axis=0), index=dataframe.index),
            ["exit_long", "exit_tag"],
        ] = (1, "ema_cross_exit")

        # === Exit SHORT: EMA cross up OR RSI oversold ===
        conditions_exit_short = [
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            (dataframe[rsi_col] < 40),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_exit_short, axis=0), index=dataframe.index),
            ["exit_short", "exit_tag"],
        ] = (1, "ema_cross_exit_short")

        return dataframe

    def custom_stoploss(self, pair: str, trade, current_time,
                        current_rate: float, current_profit: float,
                        after_fill: bool, **kwargs) -> float | None:
        """ATR-based dynamic stoploss with tighter levels."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) < 1:
            return None

        last_candle = dataframe.iloc[-1]
        atr = last_candle.get("atr", 0)
        if atr == 0:
            return None

        # Base: 1.5x ATR (was 2x)
        atr_stoploss = -(atr * 1.5) / current_rate

        if current_profit > 0.015:
            atr_stoploss = -(atr * 1.0) / current_rate
        if current_profit > 0.03:
            atr_stoploss = -(atr * 0.5) / current_rate

        return max(atr_stoploss, -0.04)  # max 4%
