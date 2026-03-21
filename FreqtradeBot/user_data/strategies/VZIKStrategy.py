"""
VZIK Crypto Strategy v1.0
RSI + EMA crossover + Volume + OBV divergence
Futures (long + short), 1h timeframe, BTC/ETH
"""

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta


class VZIKStrategy(IStrategy):
    """
    Multi-indicator strategy for BTC/ETH futures.
    - EMA 9/21 crossover for trend direction
    - RSI for overbought/oversold + divergence filter
    - OBV for volume confirmation
    - ATR-based dynamic stoploss
    """

    INTERFACE_VERSION = 3

    # Timeframe
    timeframe = "1h"

    # Can go short (futures)
    can_short = True

    # ROI table — take profit at these levels
    minimal_roi = {
        "0": 0.06,     # 6% immediately
        "60": 0.04,    # 4% after 1h
        "180": 0.025,  # 2.5% after 3h
        "360": 0.015,  # 1.5% after 6h
        "720": 0.01,   # 1% after 12h
    }

    # Stoploss
    stoploss = -0.04  # 4% max loss

    # Trailing stoploss
    trailing_stop = True
    trailing_stop_positive = 0.015  # activate at +1.5%
    trailing_stop_positive_offset = 0.025  # start trailing at +2.5%
    trailing_only_offset_is_reached = True

    # Startup candle count (need enough for EMA/RSI warmup)
    startup_candle_count = 50

    # Order time in force
    order_time_in_force = {
        "entry": "GTC",
        "exit": "GTC",
    }

    # Leverage
    leverage_long = 3
    leverage_short = 3

    # === Hyperopt parameters ===
    # EMA periods
    ema_fast = IntParameter(5, 15, default=9, space="buy", optimize=True)
    ema_slow = IntParameter(15, 30, default=21, space="buy", optimize=True)

    # RSI
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=True)
    rsi_buy = IntParameter(25, 40, default=35, space="buy", optimize=True)
    rsi_sell = IntParameter(60, 80, default=65, space="sell", optimize=True)

    # Volume filter — current volume must be N times average
    volume_factor = DecimalParameter(1.0, 3.0, default=1.2, decimals=1, space="buy", optimize=True)

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

        # === OBV (On-Balance Volume) ===
        dataframe["obv"] = ta.OBV(dataframe)
        dataframe["obv_ema"] = ta.EMA(dataframe["obv"], timeperiod=20)

        # OBV slope (momentum)
        dataframe["obv_slope"] = dataframe["obv"].diff(3)

        # === ATR for dynamic stops ===
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        # === Volume EMA ===
        dataframe["volume_ema"] = ta.EMA(dataframe["volume"], timeperiod=20)

        # === MACD for confirmation ===
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # === Bollinger Bands ===
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_lower"] = bollinger["lowerband"]
        dataframe["bb_mid"] = bollinger["middleband"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast_col = f"ema_{self.ema_fast.value}"
        ema_slow_col = f"ema_{self.ema_slow.value}"
        rsi_col = f"rsi_{self.rsi_period.value}"

        # === LONG conditions ===
        conditions_long = [
            # EMA crossover (fast above slow)
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            # Previous candle: fast was below slow (crossover just happened)
            (dataframe[ema_fast_col].shift(1) <= dataframe[ema_slow_col].shift(1)),
            # RSI not overbought
            (dataframe[rsi_col] < self.rsi_sell.value),
            # RSI recovering from oversold zone
            (dataframe[rsi_col] > self.rsi_buy.value),
            # Volume above average
            (dataframe["volume"] > dataframe["volume_ema"] * self.volume_factor.value),
            # OBV confirming uptrend
            (dataframe["obv_slope"] > 0),
            # MACD histogram positive or turning positive
            (dataframe["macdhist"] > 0),
            # Basic volume check
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_cross_long")

        # === Additional LONG: RSI bounce from oversold ===
        conditions_rsi_long = [
            # RSI was oversold
            (dataframe[rsi_col].shift(1) < 30),
            # RSI recovering
            (dataframe[rsi_col] > 30),
            # Price above lower BB (not in freefall)
            (dataframe["close"] > dataframe["bb_lower"]),
            # OBV positive
            (dataframe["obv_slope"] > 0),
            # Volume present
            (dataframe["volume"] > dataframe["volume_ema"] * 0.8),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_rsi_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi_bounce_long")

        # === SHORT conditions ===
        conditions_short = [
            # EMA crossunder (fast below slow)
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            # Previous candle: fast was above slow
            (dataframe[ema_fast_col].shift(1) >= dataframe[ema_slow_col].shift(1)),
            # RSI not oversold
            (dataframe[rsi_col] > self.rsi_buy.value),
            # RSI declining from overbought
            (dataframe[rsi_col] < self.rsi_sell.value),
            # Volume above average
            (dataframe["volume"] > dataframe["volume_ema"] * self.volume_factor.value),
            # OBV confirming downtrend
            (dataframe["obv_slope"] < 0),
            # MACD histogram negative
            (dataframe["macdhist"] < 0),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_short, axis=0), index=dataframe.index),
            ["enter_short", "enter_tag"],
        ] = (1, "ema_cross_short")

        # === Additional SHORT: RSI rejection from overbought ===
        conditions_rsi_short = [
            (dataframe[rsi_col].shift(1) > 70),
            (dataframe[rsi_col] < 70),
            (dataframe["close"] < dataframe["bb_upper"]),
            (dataframe["obv_slope"] < 0),
            (dataframe["volume"] > dataframe["volume_ema"] * 0.8),
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

        # === Exit LONG ===
        conditions_exit_long = [
            # EMA crossunder
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[rsi_col] > self.rsi_sell.value),
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_exit_long, axis=0), index=dataframe.index),
            ["exit_long", "exit_tag"],
        ] = (1, "ema_cross_exit")

        # === Exit SHORT ===
        conditions_exit_short = [
            # EMA crossover
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            (dataframe[rsi_col] < self.rsi_buy.value),
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
        """
        Dynamic stoploss based on ATR.
        Tighter stop when in profit, wider when just entered.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) < 1:
            return None

        last_candle = dataframe.iloc[-1]
        atr = last_candle.get("atr", 0)

        if atr == 0:
            return None

        # ATR-based stoploss: 2x ATR from current price
        atr_stoploss = -(atr * 2) / current_rate

        # If in profit > 2%, tighten to 1x ATR
        if current_profit > 0.02:
            atr_stoploss = -(atr * 1) / current_rate

        # If in profit > 4%, very tight: 0.5x ATR
        if current_profit > 0.04:
            atr_stoploss = -(atr * 0.5) / current_rate

        return max(atr_stoploss, -0.06)  # never wider than 6%
