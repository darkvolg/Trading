# pylint: disable=missing-module-docstring,unused-argument,attribute-defined-outside-init
"""
Daily SuperTrend — TrendRider v3 candidate (alt to Donchian).

Donchian breakout v1-v3 was parked because entries land on rally tops
(buy-the-high failure mode). SuperTrend uses the same volatility
information but enters on TREND DIRECTION FLIPS instead of price-level
breakouts:

  - When the indicator line flips from above price to below price,
    that's a trend change to UP. Entry now, on the flip, NOT at a
    multi-day high. Often this fires on a pullback or a recovery,
    not at a peak.
  - The SuperTrend line itself is the trailing stop. No separate
    Chandelier logic needed.
  - Two parameters only: ATR period, ATR multiplier.

Mechanics:
  - timeframe = 1d
  - long-only
  - Indicator: pandas_ta.supertrend(length=10, multiplier=3.0)
  - Entry: SUPERTd flips from -1 → 1 (trend turns up)
  - Exit: SUPERTd flips from 1 → -1 (trend turns down) → use_exit_signal
  - Stoploss: dynamic via custom_stoploss tracking the SuperTrend line

NOT touching `TrendRiderStrategy.py` (frozen at v2.12.1) and NOT touching
`DonchianBreakoutStrategy.py` (parked).
"""

from datetime import datetime
from typing import Optional

import pandas_ta as pta
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class SupertrendStrategy(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1d"
    process_only_new_candles = True
    can_short = False
    use_exit_signal = True
    exit_profit_only = False
    use_custom_stoploss = True

    # Wide hard floor; real exit is the SuperTrend line in custom_stoploss
    # or the trend-flip signal in populate_exit_trend.
    stoploss = -0.50
    trailing_stop = False

    minimal_roi = {"0": 100}
    startup_candle_count: int = 30

    st_period: int = 10
    st_multiplier: float = 3.0

    @property
    def st_col(self) -> str:
        return f"SUPERT_{self.st_period}_{self.st_multiplier}"

    @property
    def st_dir_col(self) -> str:
        return f"SUPERTd_{self.st_period}_{self.st_multiplier}"

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        st = pta.supertrend(
            high=dataframe["high"],
            low=dataframe["low"],
            close=dataframe["close"],
            length=self.st_period,
            multiplier=self.st_multiplier,
        )
        if st is not None and not st.empty:
            dataframe["supertrend"] = st[self.st_col]
            dataframe["supertrend_dir"] = st[self.st_dir_col]
        else:
            dataframe["supertrend"] = float("nan")
            dataframe["supertrend_dir"] = 0
        # Direction-flip detection.
        dataframe["dir_prev"] = dataframe["supertrend_dir"].shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond_flip_up = (
            (dataframe["supertrend_dir"] == 1)
            & (dataframe["dir_prev"] == -1)
        )
        dataframe.loc[cond_flip_up, ["enter_long", "enter_tag"]] = (
            1, "supertrend_flip_up",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond_flip_down = (
            (dataframe["supertrend_dir"] == -1)
            & (dataframe["dir_prev"] == 1)
        )
        dataframe.loc[cond_flip_down, "exit_long"] = 1
        return dataframe

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[float]:
        """Use the SuperTrend line as a dynamic trailing stop."""
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        except Exception:
            return None
        if dataframe is None or dataframe.empty:
            return None
        st_value = dataframe["supertrend"].iloc[-1]
        if st_value is None or st_value != st_value:  # NaN check
            return None
        st_value = float(st_value)
        if st_value <= 0 or current_rate <= 0:
            return None
        offset = (st_value - current_rate) / current_rate
        if offset >= 0:
            return -0.0001  # ST line is above price → exit immediately
        return offset
