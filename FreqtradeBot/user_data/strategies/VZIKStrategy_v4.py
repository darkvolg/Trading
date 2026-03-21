"""
VZIK Crypto Strategy v4.0

Changes from v3 (based on Hyperopt analysis Sep 2025 - Mar 2026):
- REMOVED bb_bounce_long signal (was -11.4% loss, heavily negative)
- KEPT ema_cross_long (only profitable signal at +3.5%)
- KEPT rsi_bounce_long (100% win rate in v2)
- Added EMA200 trend filter: longs only above EMA200, shorts only below
- Added 4h higher timeframe confirmation via informative_pairs()
- Widened stoploss to -0.04, more aggressive ATR-based custom_stoploss
- Added RSI overbought/oversold exits (>75 for longs, <25 for shorts)
- Added volume profile: require increasing volume over 3 candles for entries
- Made shorts even stricter (bear market shorts were mostly unprofitable)
- All parameters remain optimizable via IntParameter/DecimalParameter

v4.1 Bear Market Adaptations:
- Added is_bear flag (close < EMA200 AND SMA50 < EMA200)
- Added custom_stake_amount: reduce position to 30% in bear markets
- Added volume_ratio (volume / volume_ema_20) for cleaner volume filtering
- Added ATR percentage filter: skip entries when ATR% > 5% (extreme volatility)
"""

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, merge_informative_pair
from pandas import DataFrame
import talib.abstract as ta


class VZIKStrategy_v4(IStrategy):

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

    stoploss = -0.04  # Widened from -0.03 to reduce stop-loss kills
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.025  # Slightly wider offset
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
    rsi_buy = IntParameter(25, 40, default=30, space="buy", optimize=True)
    rsi_sell = IntParameter(60, 80, default=70, space="sell", optimize=True)
    rsi_exit_overbought = IntParameter(70, 85, default=75, space="sell", optimize=True)
    rsi_exit_oversold = IntParameter(15, 30, default=25, space="sell", optimize=True)
    volume_factor = DecimalParameter(1.0, 2.5, default=1.2, decimals=1, space="buy", optimize=True)
    adx_threshold = IntParameter(15, 35, default=18, space="buy", optimize=True)
    adx_threshold_short = IntParameter(25, 40, default=30, space="buy", optimize=True)

    def informative_pairs(self):
        """Return 4h pairs for higher timeframe trend confirmation."""
        return [
            ("BTC/USDT:USDT", "4h"),
            ("ETH/USDT:USDT", "4h"),
        ]

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
        """Reduce position size to 30% in bear markets."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) < 1:
            return proposed_stake
        last_candle = dataframe.iloc[-1]
        if last_candle.get("is_bear", 0) == 1:
            return proposed_stake * 0.3
        return proposed_stake

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- Standard EMAs (for parameter optimization) ---
        for period in range(5, 31):
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)

        # --- EMA200 trend filter ---
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
        # Volume increasing over 3 candles
        dataframe["volume_increasing"] = (
            (dataframe["volume"] > dataframe["volume"].shift(1)) &
            (dataframe["volume"].shift(1) > dataframe["volume"].shift(2))
        ).astype(int)

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
        dataframe["bb_width"] = (dataframe["bb_upper"] - dataframe["bb_lower"]) / dataframe["bb_mid"]

        # --- Stochastic RSI ---
        stoch = ta.STOCHRSI(dataframe, timeperiod=14, fastk_period=3, fastd_period=3)
        dataframe["stochrsi_k"] = stoch["fastk"]
        dataframe["stochrsi_d"] = stoch["fastd"]

        # --- EMA 50 for additional trend context ---
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)

        # --- SMA 50 for bear market detection ---
        dataframe["sma_50"] = ta.SMA(dataframe, timeperiod=50)

        # --- Bear market flag: price below EMA200 AND SMA50 below EMA200 ---
        dataframe["is_bear"] = (
            (dataframe["close"] < dataframe["ema_200"]) &
            (dataframe["sma_50"] < dataframe["ema_200"])
        ).astype(int)

        # --- Volume ratio (volume / volume_ema_20) ---
        dataframe["volume_ratio"] = dataframe["volume"] / (dataframe["volume_ema"] + 1e-10)

        # --- ATR percentage (ATR / close) for extreme volatility filter ---
        dataframe["atr_pct"] = dataframe["atr"] / (dataframe["close"] + 1e-10)

        # --- 4h Higher Timeframe Data ---
        # Merge BTC 4h data
        informative_btc = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="4h")
        if len(informative_btc) > 0:
            informative_btc["ema_50_4h"] = ta.EMA(informative_btc, timeperiod=50)
            informative_btc["ema_200_4h"] = ta.EMA(informative_btc, timeperiod=200)
            informative_btc["rsi_14_4h"] = ta.RSI(informative_btc, timeperiod=14)
            informative_btc = informative_btc[["date", "ema_50_4h", "ema_200_4h", "rsi_14_4h"]].copy()
            informative_btc.columns = ["date", "btc_ema_50_4h", "btc_ema_200_4h", "btc_rsi_14_4h"]
            dataframe = merge_informative_pair(
                dataframe, informative_btc, self.timeframe, "4h",
                ffill=True,
            )
            # Rename merged columns (merge_informative_pair adds _4h suffix)
            for col in ["btc_ema_50_4h", "btc_ema_200_4h", "btc_rsi_14_4h"]:
                merged_col = f"{col}_4h"
                if merged_col in dataframe.columns:
                    dataframe.rename(columns={merged_col: col}, inplace=True)

        # Merge ETH 4h data
        informative_eth = self.dp.get_pair_dataframe(pair="ETH/USDT:USDT", timeframe="4h")
        if len(informative_eth) > 0:
            informative_eth["ema_50_4h"] = ta.EMA(informative_eth, timeperiod=50)
            informative_eth["ema_200_4h"] = ta.EMA(informative_eth, timeperiod=200)
            informative_eth = informative_eth[["date", "ema_50_4h", "ema_200_4h"]].copy()
            informative_eth.columns = ["date", "eth_ema_50_4h", "eth_ema_200_4h"]
            dataframe = merge_informative_pair(
                dataframe, informative_eth, self.timeframe, "4h",
                ffill=True,
            )
            for col in ["eth_ema_50_4h", "eth_ema_200_4h"]:
                merged_col = f"{col}_4h"
                if merged_col in dataframe.columns:
                    dataframe.rename(columns={merged_col: col}, inplace=True)

        # --- 4h trend flags ---
        # BTC bullish on 4h: EMA50 > EMA200
        if "btc_ema_50_4h" in dataframe.columns and "btc_ema_200_4h" in dataframe.columns:
            dataframe["btc_4h_bullish"] = (
                dataframe["btc_ema_50_4h"] > dataframe["btc_ema_200_4h"]
            ).astype(int)
        else:
            dataframe["btc_4h_bullish"] = 1  # Default allow if no data

        if "btc_ema_50_4h" in dataframe.columns and "btc_ema_200_4h" in dataframe.columns:
            dataframe["btc_4h_bearish"] = (
                dataframe["btc_ema_50_4h"] < dataframe["btc_ema_200_4h"]
            ).astype(int)
        else:
            dataframe["btc_4h_bearish"] = 0

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast_col = f"ema_{self.ema_fast.value}"
        ema_slow_col = f"ema_{self.ema_slow.value}"
        rsi_col = f"rsi_{self.rsi_period.value}"

        # === LONG 1: EMA crossover (profitable signal from hyperopt) ===
        conditions_long = [
            # EMA crossover
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) <= dataframe[ema_slow_col].shift(1)),
            # RSI in valid range
            (dataframe[rsi_col] > self.rsi_buy.value),
            (dataframe[rsi_col] < self.rsi_sell.value),
            # ADX shows trend
            (dataframe["adx"] > self.adx_threshold.value),
            # Volume filter with volume factor
            (dataframe["volume"] > dataframe["volume_ema"] * self.volume_factor.value),
            # OBV confirms
            (dataframe["obv_slope"] > 0),
            # EMA200 trend filter: only long when price above EMA200
            (dataframe["close"] > dataframe["ema_200"]),
            # 4h higher timeframe: BTC must be bullish
            (dataframe["btc_4h_bullish"] == 1),
            # Volume increasing over 3 candles
            (dataframe["volume_increasing"] == 1),
            # Basic volume check
            (dataframe["volume"] > 0),
            # Skip extreme volatility (ATR > 5% of price)
            (dataframe["atr_pct"] < 0.05),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_cross_long")

        # === LONG 2: RSI bounce (100% WR in v2, keep it) ===
        conditions_rsi_long = [
            # RSI bouncing from oversold
            (dataframe[rsi_col].shift(1) < 30),
            (dataframe[rsi_col] > 30),
            # Price above lower BB (recovering)
            (dataframe["close"] > dataframe["bb_lower"]),
            # OBV confirms
            (dataframe["obv_slope"] > 0),
            # Volume present
            (dataframe["volume"] > dataframe["volume_ema"] * 0.8),
            # EMA200 trend filter: only long above EMA200
            (dataframe["close"] > dataframe["ema_200"]),
            # 4h higher timeframe: BTC must be bullish
            (dataframe["btc_4h_bullish"] == 1),
            # Volume increasing over 3 candles
            (dataframe["volume_increasing"] == 1),
            # Basic volume check
            (dataframe["volume"] > 0),
            # Skip extreme volatility (ATR > 5% of price)
            (dataframe["atr_pct"] < 0.05),
        ]

        dataframe.loc[
            pd.Series(np.all(conditions_rsi_long, axis=0), index=dataframe.index),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi_bounce_long")

        # === bb_bounce_long REMOVED — was -11.4% loss in hyperopt ===

        # === SHORT: even stricter than v3 ===
        conditions_short = [
            # EMA bearish crossover
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[ema_fast_col].shift(1) >= dataframe[ema_slow_col].shift(1)),
            # RSI elevated (overbought area for shorting)
            (dataframe[rsi_col] > 55),
            # Higher ADX threshold for shorts
            (dataframe["adx"] > self.adx_threshold_short.value),
            # Bearish DI confirmation
            (dataframe["minus_di"] > dataframe["plus_di"]),
            (dataframe["minus_di"] > 25),  # Strong bearish DI
            # Heavy volume required
            (dataframe["volume"] > dataframe["volume_ema"] * 1.8),
            # OBV confirms selling
            (dataframe["obv_slope"] < 0),
            # MACD histogram negative
            (dataframe["macdhist"] < 0),
            # Price below EMA200 — only short in confirmed downtrend
            (dataframe["close"] < dataframe["ema_200"]),
            # Price below EMA50
            (dataframe["close"] < dataframe["ema_50"]),
            # 4h higher timeframe: BTC must be bearish
            (dataframe["btc_4h_bearish"] == 1),
            # Volume increasing over 3 candles
            (dataframe["volume_increasing"] == 1),
            # Basic volume check
            (dataframe["volume"] > 0),
            # Skip extreme volatility (ATR > 5% of price)
            (dataframe["atr_pct"] < 0.05),
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

        # === Exit LONG: EMA cross down ===
        conditions_exit_long = [
            (dataframe[ema_fast_col] < dataframe[ema_slow_col]),
            (dataframe[rsi_col] > 60),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_long, axis=0), index=dataframe.index),
            ["exit_long", "exit_tag"],
        ] = (1, "ema_cross_exit")

        # === Exit LONG: RSI overbought ===
        conditions_exit_long_rsi = [
            (dataframe[rsi_col] > self.rsi_exit_overbought.value),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_long_rsi, axis=0), index=dataframe.index),
            ["exit_long", "exit_tag"],
        ] = (1, "rsi_overbought_exit")

        # === Exit SHORT: EMA cross up ===
        conditions_exit_short = [
            (dataframe[ema_fast_col] > dataframe[ema_slow_col]),
            (dataframe[rsi_col] < 40),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_short, axis=0), index=dataframe.index),
            ["exit_short", "exit_tag"],
        ] = (1, "ema_cross_exit_short")

        # === Exit SHORT: RSI oversold ===
        conditions_exit_short_rsi = [
            (dataframe[rsi_col] < self.rsi_exit_oversold.value),
            (dataframe["volume"] > 0),
        ]
        dataframe.loc[
            pd.Series(np.all(conditions_exit_short_rsi, axis=0), index=dataframe.index),
            ["exit_short", "exit_tag"],
        ] = (1, "rsi_oversold_exit")

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

        # More aggressive ATR-based stoploss
        # Default: 2x ATR (wider to avoid stop hunts)
        atr_stoploss = -(atr * 2.0) / current_rate

        # Tighten as profit grows
        if current_profit > 0.01:
            atr_stoploss = -(atr * 1.5) / current_rate
        if current_profit > 0.02:
            atr_stoploss = -(atr * 1.0) / current_rate
        if current_profit > 0.035:
            atr_stoploss = -(atr * 0.5) / current_rate

        # Never allow stoploss wider than -0.05 or tighter than -0.005
        return max(min(atr_stoploss, -0.005), -0.05)
