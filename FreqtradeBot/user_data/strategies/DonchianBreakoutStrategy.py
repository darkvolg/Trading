# pylint: disable=missing-module-docstring,unused-argument,attribute-defined-outside-init
"""
Daily Donchian Breakout — TrendRider v3 candidate (skeleton).

Inspired by Curtis Faith ("Way of the Turtle", 2007) and Andreas Clenow
("Following the Trend", 2013). Designed to leave the 1h local optimum the
old TrendRider strategy has been stuck in: 11 attempts (5 hyperopt configs +
6 structural mods) all regressed on 480d OOS. This strategy moves to a
daily timeframe and holds for weeks, with only two real parameters
(Donchian period, ATR multiplier) to keep overfitting risk minimal.

Phase 1 — skeleton only. Indicator/entry/exit/sizing logic is filled in
in subsequent sessions per STRATEGY_REDESIGN_PLAN.md.
"""

from datetime import datetime
from typing import Optional

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class DonchianBreakoutStrategy(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1d"
    process_only_new_candles = True
    can_short = False
    use_exit_signal = True
    exit_profit_only = False
    use_custom_stoploss = True

    # 10% hard floor — real exit is the ATR Chandelier in custom_stoploss.
    stoploss = -0.10
    trailing_stop = False

    # Disable Freqtrade's static ROI ladder; exits are signal-driven.
    minimal_roi = {"0": 100}

    startup_candle_count: int = 60  # need 50d Donchian + ATR(20) warmup

    # --- Phase 2 TODO -------------------------------------------------------
    # populate_indicators:
    #   donchian_upper = high.rolling(50).max().shift(1)
    #   donchian_lower = low.rolling(50).min().shift(1)
    #   atr            = ta.ATR(dataframe, timeperiod=20)
    #   highest_high   = high.cummax() (per-trade, computed in custom_exit)
    #
    # populate_entry_trend:
    #   long when close > donchian_upper (breakout) AND volume > rolling mean
    #
    # populate_exit_trend:
    #   exit when close < (highest_high_since_entry - 3 * atr)  (Chandelier)
    #
    # custom_stoploss:
    #   mirror the Chandelier rule so Freqtrade closes on stop-loss tick
    #
    # position sizing (custom_stake_amount):
    #   stake = (equity * 0.01) / (3 * atr / entry_price)
    #   1% account risk per trade, ATR-normalised.
    # ------------------------------------------------------------------------

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe

    def custom_stoploss(self, pair: str, trade, current_time: datetime,
                        current_rate: float, current_profit: float,
                        **kwargs) -> Optional[float]:
        return None
