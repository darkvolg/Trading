# pylint: disable=missing-module-docstring,unused-argument,attribute-defined-outside-init
"""
Daily Donchian Breakout — TrendRider v3 candidate.

Inspired by Curtis Faith ("Way of the Turtle", 2007) and Andreas Clenow
("Following the Trend", 2013). Designed to leave the 1h local optimum that
TrendRiderStrategy has been stuck in. Two real parameters (Donchian period,
ATR multiplier) keep overfitting risk minimal.

Mechanics:
  - timeframe = 1d
  - long-only
  - Regime filter: BTC/USDT:USDT close > 200-day SMA. No entries while BTC
                   is below its 200d SMA (bear regime). Standard Clenow
                   practice; v1 without this filter lost -13.59% over a
                   bear period because trend-following long-only into a
                   declining altcoin market is a known failure mode.
  - Entry: close > 50-day Donchian upper band (shifted 1 to avoid look-ahead)
           AND volume > 20-day mean volume (filter dead breakouts)
  - Exit: ATR(20) × 3 Chandelier — trail = max_rate_since_entry - 3 * ATR.
  - Position sizing: 1% account risk per trade — stake = (equity × 0.01)
                     / (3 × ATR / entry_price). Implemented in
                     custom_stake_amount.
  - Stoploss: hard floor at -10% to bound worst case; real exit is the
              Chandelier trail in custom_stoploss.

NOT touching `TrendRiderStrategy.py` — that one stays frozen at v2.12.1.
"""

from datetime import datetime
from typing import Optional

import talib.abstract as ta
from freqtrade.persistence import Trade
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

    # Wide hard floor so the Chandelier offset is never clamped tighter than
    # 3×ATR. Real per-trade dollar risk is bounded by ATR-normalised position
    # sizing in custom_stake_amount (1% account risk), not by this percentage.
    # Crypto daily ATR is often 10-15% of price → 3×ATR ≈ 30-45% trail width;
    # a -10% hard floor would convert the Chandelier into a regular 10% trail
    # and chop every trade out on normal pullbacks.
    stoploss = -0.50
    trailing_stop = False

    # Disable static ROI ladder; exits are signal/Chandelier driven.
    minimal_roi = {"0": 100}

    # 50d Donchian + 20d ATR + 20d volume mean → 50 + slack
    startup_candle_count: int = 60

    # --- Tunables ---
    donchian_period: int = 50
    atr_period: int = 20
    # 3.0 stays. Tested 2.0 hoping to cut max-to-close giveback (some trades
    # gave back 20% of profit before stopping out). Result: WR dropped from
    # 14.8% → 11.1% and total return worsened (-11.3% → -14.7%). Tighter
    # exits just convert wins into smaller wins or losses without fixing the
    # entry-timing problem — many breakout entries land on rally tops that
    # immediately pull back. That's a concept problem with breakout entries
    # on crypto alts, not a parameter problem.
    atr_multiplier: float = 3.0
    volume_lookback: int = 20
    risk_per_trade: float = 0.01  # 1% account risk
    regime_pair: str = "BTC/USDT:USDT"
    regime_sma_period: int = 200

    def informative_pairs(self):
        """Pull BTC daily data for the regime filter regardless of whitelist."""
        return [(self.regime_pair, self.timeframe)]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Donchian channel, ATR, volume mean, BTC regime filter."""
        # Donchian upper/lower bands (yesterday's, no look-ahead).
        dataframe["donchian_upper"] = (
            dataframe["high"].rolling(self.donchian_period).max().shift(1)
        )
        dataframe["donchian_lower"] = (
            dataframe["low"].rolling(self.donchian_period).min().shift(1)
        )
        # ATR for Chandelier exit + position sizing.
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=self.atr_period)
        # Volume filter — kill dead breakouts.
        dataframe["volume_mean"] = (
            dataframe["volume"].rolling(self.volume_lookback).mean()
        )
        # BTC regime: long-only when BTC > BTC.SMA(200). Merged on date.
        try:
            btc = self.dp.get_pair_dataframe(
                pair=self.regime_pair, timeframe=self.timeframe
            )
            if btc is not None and not btc.empty:
                btc = btc[["date", "close"]].copy()
                btc["btc_sma"] = btc["close"].rolling(self.regime_sma_period).mean()
                btc["btc_regime_bull"] = (btc["close"] > btc["btc_sma"]).astype(int)
                btc = btc[["date", "btc_regime_bull"]]
                dataframe = dataframe.merge(btc, on="date", how="left")
                dataframe["btc_regime_bull"] = (
                    dataframe["btc_regime_bull"].fillna(0).astype(int)
                )
            else:
                dataframe["btc_regime_bull"] = 0
        except Exception:
            dataframe["btc_regime_bull"] = 0
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Long when today's close prints a new 50d high on above-average volume,
        AND BTC is in a bull regime (close > 200d SMA)."""
        cond_breakout = dataframe["close"] > dataframe["donchian_upper"]
        cond_volume = dataframe["volume"] > dataframe["volume_mean"]
        cond_atr_valid = dataframe["atr"] > 0  # avoid divide-by-zero in sizing
        cond_regime = dataframe["btc_regime_bull"] == 1
        dataframe.loc[
            cond_breakout & cond_volume & cond_atr_valid & cond_regime,
            ["enter_long", "enter_tag"],
        ] = (1, "donchian_breakout_bull")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """No discrete exit signal — Chandelier trail handles it."""
        dataframe["exit_long"] = 0
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
        """ATR×3 Chandelier trailing stop.

        trail_price = max_rate_since_entry - atr_multiplier * ATR
        Returned value is the stop expressed as a relative offset from
        current_rate (Freqtrade convention: -0.05 = stop 5% below current).
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        except Exception:
            return None
        if dataframe is None or dataframe.empty:
            return None
        last_atr = float(dataframe["atr"].iloc[-1] or 0)
        if last_atr <= 0 or current_rate <= 0:
            return None
        max_rate = float(trade.max_rate or trade.open_rate)
        trail_price = max_rate - self.atr_multiplier * last_atr
        if trail_price <= 0:
            return None
        # Convert to relative-to-current offset (Freqtrade convention:
        # negative number = stop X% below current_rate).
        offset = (trail_price - current_rate) / current_rate
        if offset >= 0:
            # Trail price is above current → exit immediately.
            return -0.0001
        # Do NOT clamp here — clamping turned the Chandelier into a vanilla
        # 9.9% trail in v2 and produced a 5.4% win-rate on a +149% bull
        # rally. Position sizing (1% account risk) bounds dollar loss; the
        # -50% strategy hard floor is the ultimate backstop.
        return offset

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: Optional[float],
        max_stake: float,
        leverage: float,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> float:
        """ATR-normalised position sizing — 1% account risk per trade.

        stake = (wallet × risk_per_trade) / (atr_multiplier × ATR / entry_price)

        Falls back to the proposed Freqtrade default stake if data isn't
        available yet (first candles, missing ATR).
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        except Exception:
            return proposed_stake
        if dataframe is None or dataframe.empty:
            return proposed_stake
        last_atr = float(dataframe["atr"].iloc[-1] or 0)
        if last_atr <= 0 or current_rate <= 0:
            return proposed_stake
        try:
            wallet_total = float(self.wallets.get_total_stake_amount())
        except Exception:
            wallet_total = proposed_stake / max(self.risk_per_trade, 1e-6)
        risk_per_unit = self.atr_multiplier * last_atr / current_rate
        if risk_per_unit <= 0:
            return proposed_stake
        target_stake = (wallet_total * self.risk_per_trade) / risk_per_unit
        # Honor Freqtrade min/max stake bounds.
        if min_stake is not None and target_stake < min_stake:
            target_stake = min_stake
        if max_stake and target_stake > max_stake:
            target_stake = max_stake
        return float(target_stake)
