"""
VZIK Crypto Strategy v3.0
Balance between v2 (too conservative) and v1 (too aggressive).
- Keep strict short filters from v2
- Relax long entry slightly for more trades
- Add BB bounce long signal
- Keep RSI bounce (100% win rate in v2)
"""

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta


class VZIKStrategy_v3(IStrategy):

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = True

    minimal_roi = {
        "0": 0.05,
        "30": 0.035,
        "60": 0.025,
        "120": 0.02,
        "240": 0.015,
        "480": 0.01,
    }

    stoploss = -0.03
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    use_custom_stoploss = True
    startup_candle_count = 50
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    leverage_long = 3
    leverage_short = 2

    # Parameters
    ema_fast = IntParameter(5, 15, default=9, space="buy", optimize=True)
    ema_slow = IntParameter(15, 30, default=21, space="buy", optimize=True)
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=True)
    rsi_buy = IntParameter(25, 40, default=30, space="buy", optimize=True)
    rsi_sell = IntParameter(60, 80, default=70, space="sell", optimize=True)
    volume_factor = DecimalParameter(1.0, 2.5, default=1.2, decimals=1, space="buy", optimize=True)
    adx_threshold = IntParameter(15, 35, default=18, space="buy", optimize=True)

    def leverage(self, pair: str, current_time, current_rate: float,
                 proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        if side == "short":
            return min(self.leverage_short, max_leverage)
        return min(self.leverage_long, max_leverage)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for period in range(5, 31):
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)

        for period in range(10, 21):
            dataframe[f"rsi_{period}"] = ta.RSI(dataframe, timeperiod=period)

        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)

        dataframe["obv"] = ta.OBV(dataframe)
        dataframe["obv_ema"] = ta.EMA(dataframe["obv"], timeperiod=20)
        dataframe["obv_slope"] = dataframe["obv"].diff(3)

        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["volume_ema"] = ta.EMA(dataframe["volume"], timeperiod=20)

        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_lower"] = bollinger["lowerband"]
        dataframe["bb_mid"] = bollinger["middleband"]
        dataframe["bb_width"] = (dataframe["bb_upper"] - dataframe["bb_lower"]) / dataframe["bb_mid"]

        stoch = ta.STOCHRSI(dataframe, timeperiod=14, fastk_period=3, fastd_period=3)
        dataframe["stochrsi_k"] = stoch["fastk"]
        dataframe["stochrsi_d"] = stoch["fastd"]

        # EMA 50 for trend context
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast_col = f"ema_{self.ema_fast.value}"
        ema_slow_col = f"ema_{self.ema_slow.value}"
        rsi_col = f"rsi_{self.rsi_period.value}"

        # === LONG 1: EMA crossover (relaxed vs v2) ===
        conditions_long = [
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) <= dataframe[ema_slow_col].shift(1)),
            (dataframe[rsi_col] > self.rsi_buy.value),
            (dataframe[rsi_col] < self.rsi_sell.value),
            (dataframe["adx"] > self.adx_threshold.value),
            (dataframe["volume"] > dataframe["volume_ema"] * self.volume_factor.value),
            (dataframe["obv_slope"] > 0),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_cross_long")

        # === LONG 2: RSI bounce (star signal, 100% WR in v2) ===
        conditions_rsi_long = [
            (dataframe[rsi_col].shift(1) < 30),
            (dataframe[rsi_col] > 30),
            (dataframe["close"] > dataframe["bb_lower"]),
            (dataframe["obv_slope"] > 0),
            (dataframe["volume"] > dataframe["volume_ema"] * 0.8),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_rsi_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi_bounce_long")

        # === LONG 3: BB bounce (new signal) ===
        conditions_bb_long = [
            # Price touched or went below lower BB
            (dataframe["close"].shift(1) <= dataframe["bb_lower"].shift(1)),
            # Now recovering above it
            (dataframe["close"] > dataframe["bb_lower"]),
            # RSI not too low (not crashing)
            (dataframe[rsi_col] > 25),
            (dataframe[rsi_col] < 50),
            # Volume present
            (dataframe["volume"] > dataframe["volume_ema"] * 0.8),
            # OBV not strongly negative
            (dataframe["obv_slope"] >= 0),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_bb_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "bb_bounce_long")

        # === SHORT: very strict (from v2, shorts are risky) ===
        conditions_short = [
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) >= dataframe[ema_slow_col].shift(1)),
            (dataframe[rsi_col] > 50),
            (dataframe["adx"] > 25),
            (dataframe["minus_di"] > dataframe["plus_di"]),
            (dataframe["volume"] > dataframe["volume_ema"] * 1.5),
            (dataframe["obv_slope"] < 0),
            (dataframe["macdhist"] < 0),
            (dataframe["close"] < dataframe["ema_50"]),  # below EMA50 = downtrend
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_short, axis=0), index=dataframe.index),
            ["enter_short", "enter_tag"],
        ] = (1, "ema_cross_short")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast_col = f"ema_{self.ema_fast.value}"
        ema_slow_col = f"ema_{self.ema_slow.value}"
        rsi_col = f"rsi_{self.rsi_period.value}"

        # Exit LONG
        conditions_exit_long = [
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[rsi_col] > 60),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_long, axis=0), index=dataframe.index),
            ["exit_long", "exit_tag"],
        ] = (1, "ema_cross_exit")

        # Exit SHORT
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
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) < 1:
            return None

        last_candle = dataframe.iloc[-1]
        atr = last_candle.get("atr", 0)
        if atr == 0:
            return None

        atr_stoploss = -(atr * 1.5) / current_rate
        if current_profit > 0.015:
            atr_stoploss = -(atr * 1.0) / current_rate
        if current_profit > 0.03:
            atr_stoploss = -(atr * 0.5) / current_rate

        return max(atr_stoploss, -0.04)
