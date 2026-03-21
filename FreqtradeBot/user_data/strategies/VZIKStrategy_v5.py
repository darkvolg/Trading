"""
VZIK Crypto Strategy v5.0 — "Adaptive Bear Fighter"

Philosophy: Best of v3 (active trading) + v4 (capital preservation).
Designed for bear/sideways markets based on Sep 2025 - Mar 2026 backtests.

Key lessons applied:
- v3 had too many bad entries (106 trades, -21.6%). ROI exits were profitable
  but stops killed everything. bb_bounce_long was the worst signal.
- v4 was too strict (3 trades, -1.07%). 4h timeframe filter + volume_increasing
  + BTC correlation killed nearly all entries.
- v5 drops 4h requirement, drops bb_bounce_long, adds mean_reversion_short
  for actively profiting in bear markets, and uses regime-aware position sizing.

Regime detection (simplified from v4):
- Bear: close < EMA200 (1h only, no 4h requirement)
- Bull: close > EMA200 AND EMA50 > EMA200
- Neutral: everything else

Entry signals:
- ema_cross_long: bull/neutral only, requires ADX > 20
- rsi_bounce_long: ALL regimes (was 100% WR in v2), RSI < 25->30 cross
- mean_reversion_short (NEW): bear regime, RSI > 55 falling, BB upper touch reversal
- ema_cross_short: bear regime, relaxed from v4's too-strict conditions

Risk management:
- Stoploss -3.5% (between v3's -3% and v4's -4%)
- ATR-based custom stoploss: 1.5x normally, tightens at profit
- Position sizing: 30% in bear, 100% in bull (from v4)
- Leverage: 3x long, 2x short
"""

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta


class VZIKStrategy_v5(IStrategy):

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = True

    # ROI from v3 — was profitable on winning trades
    minimal_roi = {
        "0": 0.05,
        "30": 0.035,
        "60": 0.025,
        "120": 0.02,
        "240": 0.015,
        "480": 0.01,
    }

    stoploss = -0.035  # Between v3's -0.03 and v4's -0.04
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    use_custom_stoploss = True
    startup_candle_count = 210  # Need 200 candles for EMA200
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    leverage_long = 3
    leverage_short = 2

    # --- Optimizable Parameters ---
    ema_fast = IntParameter(5, 15, default=9, space="buy", optimize=True)
    ema_slow = IntParameter(15, 30, default=21, space="buy", optimize=True)
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=True)
    rsi_buy = IntParameter(20, 35, default=28, space="buy", optimize=True)
    rsi_sell = IntParameter(65, 80, default=72, space="sell", optimize=True)
    rsi_short_entry = IntParameter(50, 65, default=55, space="sell", optimize=True)
    adx_threshold = IntParameter(15, 30, default=20, space="buy", optimize=True)
    volume_factor = DecimalParameter(1.0, 2.0, default=1.2, decimals=1, space="buy", optimize=True)

    def leverage(self, pair: str, current_time, current_rate: float,
                 proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        if side == "short":
            return min(self.leverage_short, max_leverage)
        return min(self.leverage_long, max_leverage)

    def custom_stake_amount(self, pair: str, current_time, current_rate: float,
                            proposed_stake: float, min_stake: float | None,
                            max_stake: float, leverage: float,
                            entry_tag: str | None, side: str, **kwargs) -> float:
        """Reduce long position size in bear markets. Shorts use full stake."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) < 1:
            return proposed_stake

        last_candle = dataframe.iloc[-1]

        # In bear regime, reduce longs to 30% but keep shorts at full size
        if last_candle.get("is_bear", 0) == 1 and side == "long":
            return proposed_stake * 0.3

        return proposed_stake

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- EMAs for parameter optimization ---
        for period in range(5, 31):
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)

        # --- Key trend EMAs ---
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_200"] = ta.EMA(dataframe, timeperiod=200)

        # --- RSI for all optimizable periods ---
        for period in range(10, 21):
            dataframe[f"rsi_{period}"] = ta.RSI(dataframe, timeperiod=period)

        # --- ADX / DI ---
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)

        # --- OBV ---
        dataframe["obv"] = ta.OBV(dataframe)
        dataframe["obv_ema"] = ta.EMA(dataframe["obv"], timeperiod=20)
        dataframe["obv_slope"] = dataframe["obv"].diff(3)

        # --- ATR ---
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        # --- Volume ---
        dataframe["volume_ema"] = ta.EMA(dataframe["volume"], timeperiod=20)
        dataframe["volume_ratio"] = dataframe["volume"] / (dataframe["volume_ema"] + 1e-10)

        # --- MACD ---
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # --- Bollinger Bands ---
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_lower"] = bollinger["lowerband"]
        dataframe["bb_mid"] = bollinger["middleband"]

        # --- Regime detection (simplified: 1h only, no 4h) ---
        # Bear: price below EMA200
        dataframe["is_bear"] = (
            dataframe["close"] < dataframe["ema_200"]
        ).astype(int)

        # Bull: price above EMA200 AND EMA50 above EMA200
        dataframe["is_bull"] = (
            (dataframe["close"] > dataframe["ema_200"]) &
            (dataframe["ema_50"] > dataframe["ema_200"])
        ).astype(int)

        # Neutral: not bear and not bull (close > EMA200 but EMA50 < EMA200)
        dataframe["is_neutral"] = (
            (dataframe["is_bear"] == 0) & (dataframe["is_bull"] == 0)
        ).astype(int)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast_col = f"ema_{self.ema_fast.value}"
        ema_slow_col = f"ema_{self.ema_slow.value}"
        rsi_col = f"rsi_{self.rsi_period.value}"

        # === LONG 1: EMA crossover — bull/neutral regimes only ===
        conditions_ema_long = [
            # EMA crossover
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) <= dataframe[ema_slow_col].shift(1)),
            # RSI in valid range
            (dataframe[rsi_col] > self.rsi_buy.value),
            (dataframe[rsi_col] < self.rsi_sell.value),
            # ADX confirms trend strength
            (dataframe["adx"] > self.adx_threshold.value),
            # Volume confirmation
            (dataframe["volume"] > dataframe["volume_ema"] * self.volume_factor.value),
            # OBV confirms buying pressure
            (dataframe["obv_slope"] > 0),
            # Regime filter: only bull or neutral
            (dataframe["is_bear"] == 0),
            # Basic volume check
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_ema_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_cross_long")

        # === LONG 2: RSI bounce — ALL regimes (100% WR historically) ===
        conditions_rsi_long = [
            # RSI crosses above 30 from below 25 (stricter oversold threshold)
            (dataframe[rsi_col].shift(1) < 25),
            (dataframe[rsi_col] > 30),
            # Price above lower BB (recovering, not crashing)
            (dataframe["close"] > dataframe["bb_lower"]),
            # OBV positive (buyers stepping in)
            (dataframe["obv_slope"] > 0),
            # Volume present
            (dataframe["volume"] > dataframe["volume_ema"] * 0.8),
            # Basic volume check
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_rsi_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi_bounce_long")

        # === NO bb_bounce_long — killed performance in v3 ===

        # === SHORT 1: Mean reversion short — bear regime only (NEW) ===
        conditions_mr_short = [
            # Bear regime required
            (dataframe["is_bear"] == 1),
            # RSI was elevated and now falling (mean reversion)
            (dataframe[rsi_col].shift(1) > self.rsi_short_entry.value),
            (dataframe[rsi_col] < dataframe[rsi_col].shift(1)),
            # Price touched or exceeded upper BB then reversed down
            (dataframe["high"].shift(1) >= dataframe["bb_upper"].shift(1)),
            (dataframe["close"] < dataframe["close"].shift(1)),
            # Volume above average confirms the move
            (dataframe["volume_ratio"] > self.volume_factor.value),
            # Basic volume check
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_mr_short, axis=0), index=dataframe.index),
            ["enter_short", "enter_tag"],
        ] = (1, "mean_reversion_short")

        # === SHORT 2: EMA cross short — bear regime only (relaxed from v4) ===
        conditions_ema_short = [
            # EMA bearish crossover
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) >= dataframe[ema_slow_col].shift(1)),
            # ADX confirms trend
            (dataframe["adx"] > 22),
            # Bearish DI confirmation
            (dataframe["minus_di"] > dataframe["plus_di"]),
            # Volume confirmation (1.3x, relaxed from v4's 1.8x)
            (dataframe["volume_ratio"] > 1.3),
            # OBV confirms selling
            (dataframe["obv_slope"] < 0),
            # MACD histogram negative
            (dataframe["macdhist"] < 0),
            # Bear regime required
            (dataframe["is_bear"] == 1),
            # Basic volume check
            (dataframe["volume"] > 0),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_ema_short, axis=0), index=dataframe.index),
            ["enter_short", "enter_tag"],
        ] = (1, "ema_cross_short")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast_col = f"ema_{self.ema_fast.value}"
        ema_slow_col = f"ema_{self.ema_slow.value}"
        rsi_col = f"rsi_{self.rsi_period.value}"

        # === Exit LONG: RSI overbought ===
        conditions_exit_long_rsi = [
            (dataframe[rsi_col] > self.rsi_sell.value),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_long_rsi, axis=0), index=dataframe.index),
            ["exit_long", "exit_tag"],
        ] = (1, "rsi_overbought_exit")

        # === Exit LONG: EMA cross down ===
        conditions_exit_long_ema = [
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) >= dataframe[ema_slow_col].shift(1)),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_long_ema, axis=0), index=dataframe.index),
            ["exit_long", "exit_tag"],
        ] = (1, "ema_cross_exit")

        # === Exit LONG: Price touches upper BB (take profit) ===
        conditions_exit_long_bb = [
            (dataframe["high"] >= dataframe["bb_upper"]),
            (dataframe[rsi_col] > 60),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_long_bb, axis=0), index=dataframe.index),
            ["exit_long", "exit_tag"],
        ] = (1, "bb_upper_exit")

        # === Exit SHORT: RSI oversold ===
        conditions_exit_short_rsi = [
            (dataframe[rsi_col] < 28),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_short_rsi, axis=0), index=dataframe.index),
            ["exit_short", "exit_tag"],
        ] = (1, "rsi_oversold_exit")

        # === Exit SHORT: EMA cross up ===
        conditions_exit_short_ema = [
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) <= dataframe[ema_slow_col].shift(1)),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_short_ema, axis=0), index=dataframe.index),
            ["exit_short", "exit_tag"],
        ] = (1, "ema_cross_exit_short")

        # === Exit SHORT: Price touches lower BB (take profit) ===
        conditions_exit_short_bb = [
            (dataframe["low"] <= dataframe["bb_lower"]),
            (dataframe[rsi_col] < 40),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_short_bb, axis=0), index=dataframe.index),
            ["exit_short", "exit_tag"],
        ] = (1, "bb_lower_exit")

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

        # Default: 1.5x ATR stoploss
        atr_stoploss = -(atr * 1.5) / current_rate

        # Tighten as profit grows
        if current_profit > 0.015:
            atr_stoploss = -(atr * 1.0) / current_rate
        if current_profit > 0.03:
            atr_stoploss = -(atr * 0.5) / current_rate

        # Clamp: never wider than -4.5%, never tighter than -0.5%
        return max(min(atr_stoploss, -0.005), -0.045)
