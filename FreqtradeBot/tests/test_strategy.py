"""
Tests for TrendRiderStrategy — populate_indicators, entry/exit trends,
bot_loop_start, confirm_trade_entry, custom_exit, informative_pairs, leverage.

All Freqtrade internals (IStrategy, Trade, DataProvider) are mocked.
All external dependencies (AlertsDB, FearGreedFetcher, OnChainDataFetcher,
Telegram messaging) are also mocked so no real I/O occurs.
"""

import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Stub the entire 'freqtrade' namespace before importing the strategy.
# This prevents any attempt to import the real freqtrade package.
# ---------------------------------------------------------------------------

def _make_freqtrade_stubs():
    # Top-level package
    ft = types.ModuleType("freqtrade")
    sys.modules.setdefault("freqtrade", ft)

    # freqtrade.strategy
    ft_strategy = types.ModuleType("freqtrade.strategy")

    class _RunMode:
        value = "backtesting"

    class IStrategy:
        INTERFACE_VERSION = 3
        config: dict = {}
        dp = None
        stoploss = -0.06
        trailing_stop = True
        trailing_stop_positive = 0.03
        trailing_stop_positive_offset = 0.05
        trailing_only_offset_is_reached = True
        timeframe = "1h"
        startup_candle_count = 210
        process_only_new_candles = True
        can_short = False
        position_adjustment_enable = False
        protections = []
        minimal_roi = {}

        def __init__(self, config: dict):
            self.config = config

    class IntParameter:
        def __init__(self, low, high, default, space):
            self.value = default
            self.in_space = True

    class DecimalParameter:
        def __init__(self, low, high, default, space):
            self.value = default
            self.in_space = True

    def merge_informative_pair(df, df_info, timeframe, info_tf, ffill=True):
        """Minimal stub: just return the original df unchanged."""
        return df

    ft_strategy.IStrategy = IStrategy
    ft_strategy.IntParameter = IntParameter
    ft_strategy.DecimalParameter = DecimalParameter
    ft_strategy.merge_informative_pair = merge_informative_pair
    sys.modules.setdefault("freqtrade.strategy", ft_strategy)

    # freqtrade.persistence
    ft_persistence = types.ModuleType("freqtrade.persistence")

    class Trade:
        @staticmethod
        def get_count_open_trades():
            return 1

    ft_persistence.Trade = Trade
    sys.modules.setdefault("freqtrade.persistence", ft_persistence)


_make_freqtrade_stubs()

# ---------------------------------------------------------------------------
# Now add the strategies directory to sys.path and import the modules under test
# ---------------------------------------------------------------------------

STRATEGIES_DIR = str(Path(__file__).resolve().parent.parent / "user_data" / "strategies")
if STRATEGIES_DIR not in sys.path:
    sys.path.insert(0, STRATEGIES_DIR)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_dataframe(n: int = 300) -> pd.DataFrame:
    """Return a realistic OHLCV DataFrame with n rows."""
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    open_ = close - np.random.randn(n) * 0.2
    volume = np.abs(np.random.randn(n) * 1000) + 500
    dates = pd.date_range("2026-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame({
        "date": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def _make_strategy(config: dict | None = None) -> "TrendRiderStrategy":  # noqa: F821
    """Construct a strategy instance with all external deps mocked."""
    if config is None:
        config = {"max_open_trades": 4, "user_data_dir": "/tmp"}

    with (
        patch("trendrider_database.AlertsDB.__init__", return_value=None),
        patch("trendrider_onchain.FearGreedFetcher.__init__", return_value=None),
        patch("trendrider_onchain.OnChainDataFetcher.__init__", return_value=None),
    ):
        from TrendRiderStrategy import TrendRiderStrategy

        strat = TrendRiderStrategy.__new__(TrendRiderStrategy)
        strat.config = config
        # Replicate IntParameter / DecimalParameter defaults
        strat.ema_fast = MagicMock(value=9)
        strat.ema_slow = MagicMock(value=16)
        strat.rsi_period = MagicMock(value=16)
        strat.rsi_pullback_low = MagicMock(value=40)
        strat.rsi_pullback_high = MagicMock(value=58)
        strat.rsi_bounce = MagicMock(value=30)
        strat.rsi_exit = MagicMock(value=82)
        strat.adx_threshold = MagicMock(value=27)
        strat.volume_factor = MagicMock(value=1.014)
        strat.leverage_value = 3
        strat.stoploss = -0.06
        strat.timeframe = "1h"

        strat._db = MagicMock()
        strat._fng_fetcher = MagicMock()
        strat._onchain = MagicMock()
        strat._onchain.cache = {}

        strat.dp = None  # most tests set dp themselves
        return strat


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def strategy():
    return _make_strategy()


@pytest.fixture
def ohlcv_df():
    return _make_ohlcv_dataframe(300)


@pytest.fixture
def metadata():
    return {"pair": "ETH/USDT:USDT"}


# ---------------------------------------------------------------------------
# 1. populate_indicators
# ---------------------------------------------------------------------------

class TestPopulateIndicators:
    """Verify that populate_indicators adds all expected columns."""

    def _run(self, strategy, ohlcv_df, metadata, fng_map=None):
        strategy._fng_fetcher.fetch.return_value = fng_map or {}
        strategy.dp = None  # use fallback path (no DataProvider)
        return strategy.populate_indicators(ohlcv_df.copy(), metadata)

    # --- EMA columns ---

    def test_ema_fast_slow_columns_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "ema_9" in df.columns
        assert "ema_16" in df.columns

    def test_ema_range_5_to_30_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        for p in range(5, 31):
            assert f"ema_{p}" in df.columns, f"ema_{p} missing"

    def test_ema_50_200_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "ema_50" in df.columns
        assert "ema_200" in df.columns

    def test_ema_values_are_finite_for_most_rows(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        # After warm-up period there should be valid EMA values
        tail = df["ema_200"].dropna()
        assert len(tail) > 0
        assert tail.iloc[-1] > 0

    # --- RSI columns ---

    def test_rsi_range_10_to_20_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        for p in range(10, 21):
            assert f"rsi_{p}" in df.columns, f"rsi_{p} missing"

    def test_rsi_values_bounded_0_100(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        rsi = df["rsi_16"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all()

    # --- ADX / DI ---

    def test_adx_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "adx" in df.columns
        assert "plus_di" in df.columns
        assert "minus_di" in df.columns

    def test_adx_non_negative(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        valid = df["adx"].dropna()
        assert (valid >= 0).all()

    # --- MACD ---

    def test_macd_columns_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        for col in ("macd", "macdsignal", "macdhist", "macdhist_prev"):
            assert col in df.columns, f"{col} missing"

    def test_macdhist_prev_is_shifted(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        # macdhist_prev should equal macdhist shifted by 1
        hist = df["macdhist"].dropna()
        df["macdhist_prev"].dropna()
        # The last value of prev equals the second-to-last value of hist
        if len(hist) > 2:
            assert abs(df["macdhist_prev"].iloc[-1] - df["macdhist"].iloc[-2]) < 1e-9

    # --- Bollinger Bands ---

    def test_bollinger_columns_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        for col in ("bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_width_sma"):
            assert col in df.columns, f"{col} missing"

    def test_bollinger_ordering(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        valid = df.dropna(subset=["bb_upper", "bb_middle", "bb_lower"])
        assert (valid["bb_upper"] >= valid["bb_middle"]).all()
        assert (valid["bb_middle"] >= valid["bb_lower"]).all()

    def test_bb_width_non_negative(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert (df["bb_width"].dropna() >= 0).all()

    # --- Volume ---

    def test_volume_columns_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "volume_ema" in df.columns
        assert "volume_ratio" in df.columns

    def test_volume_ratio_non_negative(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        valid = df["volume_ratio"].dropna()
        assert (valid >= 0).all()

    # --- OBV & ATR ---

    def test_obv_atr_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "obv" in df.columns
        assert "obv_ema" in df.columns
        assert "atr" in df.columns

    # --- Regime columns ---

    def test_is_bull_is_bear_binary(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "is_bull" in df.columns
        assert "is_bear" in df.columns
        assert set(df["is_bull"].unique()).issubset({0, 1})
        assert set(df["is_bear"].unique()).issubset({0, 1})

    def test_is_bull_is_bear_not_both_simultaneously(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        both = (df["is_bull"] == 1) & (df["is_bear"] == 1)
        assert not both.any(), "is_bull and is_bear cannot both be 1"

    def test_pullback_to_ema_column_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "pullback_to_ema" in df.columns
        assert set(df["pullback_to_ema"].unique()).issubset({0, 1})

    def test_ema50_bounce_column_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "ema50_bounce" in df.columns

    # --- MTF safety fallback (dp=None) ---

    def test_mtf_fallback_columns_present_when_dp_is_none(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        for col in ("is_bull_4h", "rsi_14_4h", "adx_4h", "btc_is_bull_1h", "btc_rsi_1h", "ema_200_1d"):
            assert col in df.columns, f"Fallback column {col} missing"

    def test_btc_rsi_1h_fallback_value_is_50(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert (df["btc_rsi_1h"] == 50).all()

    # --- Fear & Greed Index ---

    def test_fng_value_column_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "fng_value" in df.columns

    def test_fng_value_defaults_to_50_when_api_returns_empty(self, strategy, ohlcv_df, metadata):
        strategy._fng_fetcher.fetch.return_value = {}
        df = self._run(strategy, ohlcv_df, metadata)
        assert (df["fng_value"] == 50).all()

    def test_fng_value_uses_fetcher_data(self, strategy, ohlcv_df, metadata):
        # Use the actual first date present in the generated dataframe
        df_dates = ohlcv_df["date"].dt.strftime("%Y-%m-%d")
        date_str = df_dates.iloc[0]
        fng_map = {date_str: 75}
        # Pass fng_map directly so _run does not reset it to {}
        df = self._run(strategy, ohlcv_df, metadata, fng_map=fng_map)
        matching = df[df["date"].dt.strftime("%Y-%m-%d") == date_str]["fng_value"]
        assert len(matching) > 0
        assert matching.iloc[0] == 75

    # --- On-chain columns (backtest path, dp=None) ---

    def test_funding_rate_column_present(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert "funding_rate" in df.columns
        assert "funding_extreme" in df.columns
        assert "oi_change" in df.columns

    def test_funding_rate_zero_in_backtesting(self, strategy, ohlcv_df, metadata):
        df = self._run(strategy, ohlcv_df, metadata)
        assert (df["funding_rate"] == 0.0).all()


# ---------------------------------------------------------------------------
# 2. populate_entry_trend
# ---------------------------------------------------------------------------

class TestPopulateEntryTrend:
    """Verify entry signal logic for all three LONG conditions."""

    def _indicators(self, strategy, df, metadata):
        """Run populate_indicators with mocked dp=None, then return df."""
        strategy._fng_fetcher.fetch.return_value = {}
        strategy.dp = None
        return strategy.populate_indicators(df, metadata)

    def _set_all_neutral(self, df):
        """Force all rows into a 'neutral' state — no entry triggers fire."""
        df["is_bull"] = 0
        df["pullback_to_ema"] = 0
        df["ema50_bounce"] = 0
        for col in df.columns:
            if col.startswith("rsi_"):
                df[col] = 50.0
        df["adx"] = 10.0
        df["volume_ratio"] = 0.5
        df["plus_di"] = 10.0
        df["minus_di"] = 20.0
        df["obv"] = 1000.0
        df["obv_ema"] = 2000.0
        df["volume"] = 1.0
        df["btc_rsi_1h"] = 50.0
        df["fng_value"] = 50.0
        df["macdhist"] = 0.001  # small positive to avoid zero-crossing triggers
        # Ensure close < ema_50 and ema_200 to block new signal triggers in neutral state
        df["ema_50"] = df["close"] * 2
        df["ema_200"] = df["close"] * 2
        # Neutralize EMA fast/slow crossover: set them equal
        for period in range(5, 31):
            df[f"ema_{period}"] = df["close"]
        # Ensure close is within BB bands (no BB bounce triggers)
        df["bb_lower"] = df["close"] * 0.5
        df["bb_upper"] = df["close"] * 1.5
        return df

    def _run_entry(self, strategy, df, metadata):
        df["enter_long"] = 0
        df["enter_tag"] = ""
        return strategy.populate_entry_trend(df, metadata)

    # --- trend_pullback ---

    def test_trend_pullback_fires_when_all_conditions_met(self, strategy, ohlcv_df, metadata):
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        # Force bullish setup for a single row
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 1
        df.loc[idx, "pullback_to_ema"] = 1
        df.loc[idx, rsi_col] = 45.0   # between rsi_pullback_low (40) and high (58)
        df.loc[idx, "adx"] = 30.0     # above adx_threshold (27)
        df.loc[idx, "volume_ratio"] = 1.5  # above volume_factor (1.014)
        df.loc[idx, "plus_di"] = 30.0
        df.loc[idx, "minus_di"] = 10.0
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "btc_rsi_1h"] = 50.0  # above BTC_RSI_LONG_MIN (35)
        df.loc[idx, "fng_value"] = 50.0   # between 25 and 85

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 1
        assert df.loc[idx, "enter_tag"] == "trend_pullback"

    def test_trend_pullback_blocked_by_is_bull_false(self, strategy, ohlcv_df, metadata):
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        # Same as above but is_bull=0
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 0
        df.loc[idx, "pullback_to_ema"] = 1
        df.loc[idx, rsi_col] = 45.0
        df.loc[idx, "adx"] = 30.0
        df.loc[idx, "volume_ratio"] = 1.5
        df.loc[idx, "plus_di"] = 30.0
        df.loc[idx, "minus_di"] = 10.0
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 50.0

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 0

    def test_trend_pullback_blocked_by_adx_below_threshold(self, strategy, ohlcv_df, metadata):
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 1
        df.loc[idx, "pullback_to_ema"] = 1
        df.loc[idx, rsi_col] = 45.0
        df.loc[idx, "adx"] = 10.0  # below threshold (27)
        df.loc[idx, "volume_ratio"] = 1.5
        df.loc[idx, "plus_di"] = 30.0
        df.loc[idx, "minus_di"] = 10.0
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 50.0

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 0

    def test_trend_pullback_blocked_by_low_volume(self, strategy, ohlcv_df, metadata):
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 1
        df.loc[idx, "pullback_to_ema"] = 1
        df.loc[idx, rsi_col] = 45.0
        df.loc[idx, "adx"] = 30.0
        df.loc[idx, "volume_ratio"] = 0.5  # below volume_factor (1.014)
        df.loc[idx, "plus_di"] = 30.0
        df.loc[idx, "minus_di"] = 10.0
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 50.0

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 0

    def test_trend_pullback_blocked_by_extreme_fear(self, strategy, ohlcv_df, metadata):
        """FNG below FNG_HEALTHY_MIN (25) should block entry."""
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 1
        df.loc[idx, "pullback_to_ema"] = 1
        df.loc[idx, rsi_col] = 45.0
        df.loc[idx, "adx"] = 30.0
        df.loc[idx, "volume_ratio"] = 1.5
        df.loc[idx, "plus_di"] = 30.0
        df.loc[idx, "minus_di"] = 10.0
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 10.0  # extreme fear — below 25

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 0

    def test_trend_pullback_blocked_by_extreme_greed(self, strategy, ohlcv_df, metadata):
        """FNG above FNG_HEALTHY_MAX (85) should block entry."""
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 1
        df.loc[idx, "pullback_to_ema"] = 1
        df.loc[idx, rsi_col] = 45.0
        df.loc[idx, "adx"] = 30.0
        df.loc[idx, "volume_ratio"] = 1.5
        df.loc[idx, "plus_di"] = 30.0
        df.loc[idx, "minus_di"] = 10.0
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 90.0  # extreme greed — above 85

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 0

    def test_trend_pullback_blocked_by_btc_rsi_too_low(self, strategy, ohlcv_df, metadata):
        """BTC RSI below BTC_RSI_LONG_MIN (35) should block entry."""
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 1
        df.loc[idx, "pullback_to_ema"] = 1
        df.loc[idx, rsi_col] = 45.0
        df.loc[idx, "adx"] = 30.0
        df.loc[idx, "volume_ratio"] = 1.5
        df.loc[idx, "plus_di"] = 30.0
        df.loc[idx, "minus_di"] = 10.0
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "btc_rsi_1h"] = 20.0  # below BTC_RSI_LONG_MIN (35)
        df.loc[idx, "fng_value"] = 50.0

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 0

    # --- ema50_bounce ---

    def test_ema50_bounce_fires_when_conditions_met(self, strategy, ohlcv_df, metadata):
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 1
        df.loc[idx, "ema50_bounce"] = 1
        df.loc[idx, rsi_col] = 40.0      # between 30 and 50
        df.loc[idx, "adx"] = 25.0        # above 20
        df.loc[idx, "volume_ratio"] = 1.2  # above 1.0
        df.loc[idx, "macdhist"] = 0.01
        # Ensure macdhist is increasing (shift trick — set prev row lower)
        df.loc[idx - 1, "macdhist"] = -0.01
        df.loc[idx, "volume"] = 100.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 50.0

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 1
        assert df.loc[idx, "enter_tag"] == "ema50_bounce"

    def test_ema50_bounce_blocked_when_rsi_above_50(self, strategy, ohlcv_df, metadata):
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "is_bull"] = 1
        df.loc[idx, "ema50_bounce"] = 1
        df.loc[idx, rsi_col] = 55.0  # above 50 — blocked
        df.loc[idx, "adx"] = 25.0
        df.loc[idx, "volume_ratio"] = 1.2
        df.loc[idx, "macdhist"] = 0.01
        df.loc[idx - 1, "macdhist"] = -0.01
        df.loc[idx, "volume"] = 100.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 50.0

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 0

    # --- rsi_bounce ---

    def test_rsi_bounce_fires_when_rsi_crosses_above_threshold(self, strategy, ohlcv_df, metadata):
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        # Force close > ema_200
        df.loc[idx, "ema_200"] = 50.0
        df.loc[idx, "close"] = 100.0
        # RSI crosses above rsi_bounce (30): prev < 30, current > 30
        df.loc[idx - 1, rsi_col] = 28.0
        df.loc[idx, rsi_col] = 32.0
        # close > bb_lower
        df.loc[idx, "bb_lower"] = 80.0
        # Bullish candle
        df.loc[idx, "open"] = 95.0
        df.loc[idx, "close"] = 100.0
        df.loc[idx, "volume_ratio"] = 1.0  # above 0.8
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "volume"] = 500.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 50.0

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 1
        assert df.loc[idx, "enter_tag"] == "rsi_bounce"

    def test_rsi_bounce_not_fires_when_below_ema200(self, strategy, ohlcv_df, metadata):
        """close < ema_200 blocks rsi_bounce."""
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, "ema_200"] = 200.0
        df.loc[idx, "close"] = 100.0   # below ema_200
        df.loc[idx - 1, rsi_col] = 28.0
        df.loc[idx, rsi_col] = 32.0
        df.loc[idx, "bb_lower"] = 80.0
        df.loc[idx, "open"] = 95.0
        df.loc[idx, "volume_ratio"] = 1.0
        df.loc[idx, "obv"] = 2000.0
        df.loc[idx, "obv_ema"] = 1000.0
        df.loc[idx, "volume"] = 500.0
        df.loc[idx, "btc_rsi_1h"] = 50.0
        df.loc[idx, "fng_value"] = 50.0

        df = self._run_entry(strategy, df, metadata)
        assert df.loc[idx, "enter_long"] == 0

    def test_no_signal_by_default_on_neutral_bars(self, strategy, ohlcv_df, metadata):
        """All-neutral dataframe should produce no entry signals."""
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._set_all_neutral(df)
        df = self._run_entry(strategy, df, metadata)
        assert (df["enter_long"] == 0).all()

    def test_enter_long_column_exists(self, strategy, ohlcv_df, metadata):
        df = self._indicators(strategy, ohlcv_df, metadata)
        df = self._run_entry(strategy, df, metadata)
        assert "enter_long" in df.columns
        assert "enter_tag" in df.columns


# ---------------------------------------------------------------------------
# 3. populate_exit_trend
# ---------------------------------------------------------------------------

class TestPopulateExitTrend:
    """Verify all three exit conditions."""

    def _prep(self, strategy, ohlcv_df, metadata):
        strategy._fng_fetcher.fetch.return_value = {}
        strategy.dp = None
        df = strategy.populate_indicators(ohlcv_df.copy(), metadata)
        df["exit_long"] = 0
        df["exit_tag"] = ""
        return df

    def _run(self, strategy, df, metadata):
        return strategy.populate_exit_trend(df, metadata)

    # --- rsi_overbought ---

    def test_rsi_overbought_triggers_exit(self, strategy, ohlcv_df, metadata):
        df = self._prep(strategy, ohlcv_df, metadata)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, rsi_col] = 90.0   # above rsi_exit (82)
        df.loc[idx, "volume"] = 500.0
        df = self._run(strategy, df, metadata)
        assert df.loc[idx, "exit_long"] == 1
        assert df.loc[idx, "exit_tag"] == "rsi_overbought"

    def test_rsi_overbought_does_not_trigger_below_threshold(self, strategy, ohlcv_df, metadata):
        df = self._prep(strategy, ohlcv_df, metadata)
        len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df[rsi_col] = 50.0  # well below exit threshold
        df = self._run(strategy, df, metadata)
        # rsi_overbought condition should not fire
        rsi_exits = df[df["exit_tag"] == "rsi_overbought"]
        assert len(rsi_exits) == 0

    def test_rsi_overbought_blocked_when_volume_zero(self, strategy, ohlcv_df, metadata):
        df = self._prep(strategy, ohlcv_df, metadata)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df.loc[idx, rsi_col] = 90.0
        df.loc[idx, "volume"] = 0.0  # blocked by volume > 0 guard
        df = self._run(strategy, df, metadata)
        assert df.loc[idx, "exit_long"] == 0

    # --- ema_bearish_cross ---

    def test_ema_bearish_cross_triggers_exit(self, strategy, ohlcv_df, metadata):
        df = self._prep(strategy, ohlcv_df, metadata)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        ema_fast_col = f"ema_{strategy.ema_fast.value}"
        ema_slow_col = f"ema_{strategy.ema_slow.value}"
        # Current: fast < slow (bearish cross)
        df.loc[idx, ema_fast_col] = 99.0
        df.loc[idx, ema_slow_col] = 100.0
        # Previous: fast >= slow (just crossed)
        df.loc[idx - 1, ema_fast_col] = 101.0
        df.loc[idx - 1, ema_slow_col] = 100.0
        # MACD hist negative
        df.loc[idx, "macdhist"] = -0.01
        # RSI above 50 (still elevated)
        df.loc[idx, rsi_col] = 60.0
        df.loc[idx, "volume"] = 500.0

        df = self._run(strategy, df, metadata)
        assert df.loc[idx, "exit_long"] == 1
        assert df.loc[idx, "exit_tag"] == "ema_bearish_cross"

    def test_ema_bearish_cross_not_triggered_without_macd_confirmation(self, strategy, ohlcv_df, metadata):
        df = self._prep(strategy, ohlcv_df, metadata)
        idx = len(df) - 2
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        ema_fast_col = f"ema_{strategy.ema_fast.value}"
        ema_slow_col = f"ema_{strategy.ema_slow.value}"
        df.loc[idx, ema_fast_col] = 99.0
        df.loc[idx, ema_slow_col] = 100.0
        df.loc[idx - 1, ema_fast_col] = 101.0
        df.loc[idx - 1, ema_slow_col] = 100.0
        df.loc[idx, "macdhist"] = 0.01   # positive MACD — no confirmation
        df.loc[idx, rsi_col] = 60.0
        df.loc[idx, "volume"] = 500.0

        df = self._run(strategy, df, metadata)
        assert df.loc[idx, "exit_tag"] != "ema_bearish_cross"

    # --- trend_broken ---

    def test_trend_broken_triggers_when_both_candles_below_threshold(self, strategy, ohlcv_df, metadata):
        """trend_broken fires when both current and previous close < ema_200 * 0.97."""
        df = self._prep(strategy, ohlcv_df, metadata)
        idx = len(df) - 2
        # Both candles well below ema_200 * 0.97 = 97.0 threshold
        df.loc[idx, "close"] = 80.0
        df.loc[idx, "ema_200"] = 100.0
        df.loc[idx - 1, "close"] = 85.0
        df.loc[idx - 1, "ema_200"] = 100.0
        df.loc[idx, "volume"] = 500.0

        df = self._run(strategy, df, metadata)
        assert df.loc[idx, "exit_long"] == 1
        assert df.loc[idx, "exit_tag"] == "trend_broken"

    def test_trend_broken_not_triggered_when_previous_above_threshold(self, strategy, ohlcv_df, metadata):
        """trend_broken requires both candles below ema_200 * 0.97; previous above = no trigger."""
        df = self._prep(strategy, ohlcv_df, metadata)
        idx = len(df) - 2
        # Current below threshold, but previous above it (99 > 97)
        df.loc[idx, "close"] = 80.0
        df.loc[idx, "ema_200"] = 100.0
        df.loc[idx - 1, "close"] = 99.0
        df.loc[idx - 1, "ema_200"] = 100.0
        df.loc[idx, "volume"] = 500.0

        df = self._run(strategy, df, metadata)
        assert df.loc[idx, "exit_tag"] != "trend_broken"

    # --- general ---

    def test_exit_columns_always_present(self, strategy, ohlcv_df, metadata):
        df = self._prep(strategy, ohlcv_df, metadata)
        df = self._run(strategy, df, metadata)
        assert "exit_long" in df.columns
        assert "exit_tag" in df.columns


# ---------------------------------------------------------------------------
# 4. bot_loop_start
# ---------------------------------------------------------------------------

class TestBotLoopStart:
    """Verify bot_loop_start: on-chain fetches, cooldown, price-alert logic."""

    def _make_dp(self, mode="backtesting", whitelist=None, dataframe=None, analyzed=None):
        dp = MagicMock()
        dp.runmode = MagicMock()
        dp.runmode.value = mode
        dp.current_whitelist.return_value = whitelist or ["ETH/USDT:USDT"]
        if analyzed is not None:
            dp.get_analyzed_dataframe.return_value = (analyzed, {})
        else:
            dp.get_analyzed_dataframe.return_value = (pd.DataFrame(), {})
        return dp

    def test_no_dp_returns_immediately(self, strategy):
        strategy.dp = None
        # Should not raise
        strategy.bot_loop_start(datetime.now(timezone.utc))

    def test_onchain_fetch_called_for_live_mode(self, strategy):
        pair = "ETH/USDT:USDT"
        strategy.dp = self._make_dp(mode="live", whitelist=[pair])
        strategy._db.get_last_alert.return_value = None
        strategy.bot_loop_start(datetime.now(timezone.utc))
        strategy._onchain.fetch_funding_rate.assert_called_once_with(pair)
        strategy._onchain.fetch_open_interest.assert_called_once_with(pair)

    def test_onchain_fetch_called_for_dry_run_mode(self, strategy):
        pair = "BTC/USDT:USDT"
        strategy.dp = self._make_dp(mode="dry_run", whitelist=[pair])
        strategy._db.get_last_alert.return_value = None
        strategy.bot_loop_start(datetime.now(timezone.utc))
        strategy._onchain.fetch_funding_rate.assert_called_with(pair)

    def test_onchain_fetch_not_called_in_backtesting(self, strategy):
        pair = "ETH/USDT:USDT"
        strategy.dp = self._make_dp(mode="backtesting", whitelist=[pair])
        strategy._db.get_last_alert.return_value = None
        strategy.bot_loop_start(datetime.now(timezone.utc))
        strategy._onchain.fetch_funding_rate.assert_not_called()

    def test_onchain_fetch_exception_is_swallowed(self, strategy):
        pair = "ETH/USDT:USDT"
        strategy.dp = self._make_dp(mode="live", whitelist=[pair])
        strategy._onchain.fetch_funding_rate.side_effect = RuntimeError("network error")
        strategy._db.get_last_alert.return_value = None
        # Must not raise
        strategy.bot_loop_start(datetime.now(timezone.utc))

    def test_alert_skipped_within_cooldown_period(self, strategy):
        pair = "ETH/USDT:USDT"
        now = datetime.now(timezone.utc)
        # Last alert was only 1 hour ago (cooldown is 4h = 14400s)
        recent = datetime(now.year, now.month, now.day, max(now.hour - 1, 0), tzinfo=timezone.utc)
        strategy._db.get_last_alert.return_value = recent
        strategy.dp = self._make_dp(mode="backtesting", whitelist=[pair])
        strategy.bot_loop_start(now)
        # dp.get_analyzed_dataframe should NOT be called because still in cooldown
        strategy.dp.get_analyzed_dataframe.assert_not_called()

    def test_alert_sent_when_cooldown_expired(self, strategy, ohlcv_df, metadata):
        pair = "ETH/USDT:USDT"
        now = datetime.now(timezone.utc)
        # Last alert was 5 hours ago — beyond the 4h cooldown
        old_alert = datetime(2020, 1, 1, tzinfo=timezone.utc)
        strategy._db.get_last_alert.return_value = old_alert

        # Build a df with EMA values so proximity check fires
        df = ohlcv_df.copy()
        ema_slow_col = f"ema_{strategy.ema_slow.value}"
        close_val = 100.0
        ema_val = 99.5  # dist_ema ≈ 0.5% — within EMA_PROXIMITY_PCT (1.5%)
        df[ema_slow_col] = ema_val
        df["ema_50"] = ema_val
        df["close"] = close_val
        df["is_bull"] = 1
        rsi_col = f"rsi_{strategy.rsi_period.value}"
        df[rsi_col] = 45.0
        df["adx"] = 30.0
        df["volume_ratio"] = 1.5

        dp = self._make_dp(mode="backtesting", whitelist=[pair], analyzed=df)
        strategy.dp = dp

        with patch("TrendRiderStrategy.format_price_alert", return_value="alert_msg") as mock_fmt:
            strategy.bot_loop_start(now)

        mock_fmt.assert_called_once()
        strategy.dp.send_msg.assert_called_once()
        strategy._db.set_last_alert.assert_called_once_with(pair, now)

    def test_short_dataframe_skipped(self, strategy):
        pair = "ETH/USDT:USDT"
        strategy._db.get_last_alert.return_value = None
        short_df = pd.DataFrame({"close": [100.0]})  # only 1 row — too short
        strategy.dp = self._make_dp(mode="backtesting", whitelist=[pair], analyzed=short_df)
        strategy.bot_loop_start(datetime.now(timezone.utc))
        strategy.dp.send_msg.assert_not_called()

    def test_alert_not_sent_when_not_bull(self, strategy, ohlcv_df):
        pair = "ETH/USDT:USDT"
        strategy._db.get_last_alert.return_value = None
        df = ohlcv_df.copy()
        df["is_bull"] = 0  # bearish
        strategy.dp = self._make_dp(mode="backtesting", whitelist=[pair], analyzed=df)
        strategy.bot_loop_start(datetime.now(timezone.utc))
        strategy.dp.send_msg.assert_not_called()


# ---------------------------------------------------------------------------
# 5. confirm_trade_entry
# ---------------------------------------------------------------------------

class TestConfirmTradeEntry:
    """Verify confirm_trade_entry: confidence check, signal dispatch, return value."""

    def _make_last_candle(self, conf_numeric=7):
        """Return a candle dict that yields the requested confidence score."""
        return {
            "close": 100.0,
            f"rsi_{16}": 45.0,
            "adx": 35.0,
            "volume_ratio": 1.8,
            "macdhist": 0.005,
            "macdhist_prev": 0.003,
            "obv": 1500.0,
            "obv_ema": 1400.0,
            "btc_rsi_1h": 58.0,
            "btc_is_bull_1h": 1,
            "is_bull_4h": 1,
            "adx_4h": 25.0,
            "bb_lower": 95.0,
            "bb_upper": 110.0,
            "bb_width": 0.15,
            "bb_width_sma": 0.10,
            "plus_di": 30.0,
            "minus_di": 15.0,
            "fng_value": 50,
            "funding_rate": 0.00005,
            "ema_200": 90.0,
            "ema_50": 97.0,
            "ema_20": 99.0,
            "ema_9": 99.5,
            "is_bull": 1,
        }

    def _setup_dp(self, strategy, last_candle):
        df = pd.DataFrame([last_candle])
        dp = MagicMock()
        dp.get_analyzed_dataframe.return_value = (df, {})
        strategy.dp = dp

    def test_returns_true_when_confidence_sufficient(self, strategy):
        last = self._make_last_candle()
        self._setup_dp(strategy, last)
        strategy._db.next_signal_number.return_value = 1

        with (
            patch("TrendRiderStrategy.calc_confidence", return_value=("STRONG", "||||| 7/10", ["RSI ok"], 7)),
            patch("TrendRiderStrategy.market_context", return_value="BTC: Bullish"),
            patch("TrendRiderStrategy.get_market_regime", return_value="Trending Bull"),
            patch("TrendRiderStrategy.get_estimated_hold", return_value="2-6h"),
            patch("TrendRiderStrategy.build_detailed_reason", return_value="reason"),
            patch("TrendRiderStrategy.format_entry_signal", return_value="entry_msg"),
            patch("TrendRiderStrategy.format_cornix_signal", return_value="cornix_msg"),
        ):
            result = strategy.confirm_trade_entry(
                pair="ETH/USDT:USDT",
                order_type="limit",
                amount=1.0,
                rate=100.0,
                time_in_force="gtc",
                current_time=datetime.now(timezone.utc),
                entry_tag="trend_pullback",
                side="long",
            )

        assert result is True

    def test_returns_false_when_confidence_below_minimum(self, strategy):
        last = self._make_last_candle()
        self._setup_dp(strategy, last)

        with (
            patch("TrendRiderStrategy.calc_confidence", return_value=("WEAK", "| 2/10", [], 2)),
            patch("TrendRiderStrategy.market_context", return_value="BTC: Bearish"),
            patch("TrendRiderStrategy.get_market_regime", return_value="Trending Bull"),
            patch("TrendRiderStrategy.get_estimated_hold", return_value="24-48h"),
            patch("TrendRiderStrategy.build_detailed_reason", return_value="reason"),
        ):
            result = strategy.confirm_trade_entry(
                pair="ETH/USDT:USDT",
                order_type="limit",
                amount=1.0,
                rate=100.0,
                time_in_force="gtc",
                current_time=datetime.now(timezone.utc),
                entry_tag="trend_pullback",
                side="long",
            )

        assert result is False

    def test_higher_threshold_in_bear_regime(self, strategy):
        """In bear regime CONFIDENCE_MIN_BEAR (6) is used; confidence 5 should reject."""
        last = self._make_last_candle()
        self._setup_dp(strategy, last)

        with (
            patch("TrendRiderStrategy.calc_confidence", return_value=("MEDIUM", "||||| 5/10", [], 5)),
            patch("TrendRiderStrategy.market_context", return_value="BTC: Bearish"),
            patch("TrendRiderStrategy.get_market_regime", return_value="Trending Bear"),
            patch("TrendRiderStrategy.get_estimated_hold", return_value="24-48h"),
            patch("TrendRiderStrategy.build_detailed_reason", return_value="reason"),
        ):
            result = strategy.confirm_trade_entry(
                pair="ETH/USDT:USDT",
                order_type="limit",
                amount=1.0,
                rate=100.0,
                time_in_force="gtc",
                current_time=datetime.now(timezone.utc),
                entry_tag="trend_pullback",
                side="long",
            )

        assert result is False

    def test_signal_messages_sent_to_dp(self, strategy):
        last = self._make_last_candle()
        self._setup_dp(strategy, last)
        strategy._db.next_signal_number.return_value = 42

        with (
            patch("TrendRiderStrategy.calc_confidence", return_value=("STRONG", "8/10", [], 8)),
            patch("TrendRiderStrategy.market_context", return_value="ctx"),
            patch("TrendRiderStrategy.get_market_regime", return_value="Trending Bull"),
            patch("TrendRiderStrategy.get_estimated_hold", return_value="2-6h"),
            patch("TrendRiderStrategy.build_detailed_reason", return_value="reason"),
            patch("TrendRiderStrategy.format_entry_signal", return_value="ENTRY_MSG"),
            patch("TrendRiderStrategy.format_cornix_signal", return_value="CORNIX_MSG"),
        ):
            strategy.confirm_trade_entry(
                pair="ETH/USDT:USDT",
                order_type="limit",
                amount=1.0,
                rate=100.0,
                time_in_force="gtc",
                current_time=datetime.now(timezone.utc),
                entry_tag="trend_pullback",
                side="long",
            )

        calls = [c[0][0] for c in strategy.dp.send_msg.call_args_list]
        assert "ENTRY_MSG" in calls
        assert "CORNIX_MSG" in calls

    def test_signal_queued_in_database(self, strategy):
        last = self._make_last_candle()
        self._setup_dp(strategy, last)
        strategy._db.next_signal_number.return_value = 5

        with (
            patch("TrendRiderStrategy.calc_confidence", return_value=("GOOD", "7/10", [], 7)),
            patch("TrendRiderStrategy.market_context", return_value="ctx"),
            patch("TrendRiderStrategy.get_market_regime", return_value="Trending Bull"),
            patch("TrendRiderStrategy.get_estimated_hold", return_value="6-24h"),
            patch("TrendRiderStrategy.build_detailed_reason", return_value="reason"),
            patch("TrendRiderStrategy.format_entry_signal", return_value="entry"),
            patch("TrendRiderStrategy.format_cornix_signal", return_value="cornix"),
        ):
            strategy.confirm_trade_entry(
                pair="ETH/USDT:USDT",
                order_type="limit",
                amount=1.0,
                rate=100.0,
                time_in_force="gtc",
                current_time=datetime.now(timezone.utc),
                entry_tag="trend_pullback",
                side="long",
            )

        strategy._db.queue_signal.assert_called_once()
        call_kwargs = strategy._db.queue_signal.call_args
        assert call_kwargs[0][0] == 5  # signal_num

    def test_empty_dataframe_still_returns_based_on_confidence(self, strategy):
        """When dp returns empty df, confidence check still runs with zeros."""
        dp = MagicMock()
        dp.get_analyzed_dataframe.return_value = (pd.DataFrame(), {})
        strategy.dp = dp

        with (
            patch("TrendRiderStrategy.calc_confidence", return_value=("STRONG", "8/10", [], 8)),
            patch("TrendRiderStrategy.market_context", return_value="ctx"),
            patch("TrendRiderStrategy.get_market_regime", return_value="Trending Bull"),
            patch("TrendRiderStrategy.get_estimated_hold", return_value="2-6h"),
            patch("TrendRiderStrategy.build_detailed_reason", return_value="reason"),
            patch("TrendRiderStrategy.format_entry_signal", return_value="entry"),
            patch("TrendRiderStrategy.format_cornix_signal", return_value="cornix"),
        ):
            strategy._db.next_signal_number.return_value = 1
            result = strategy.confirm_trade_entry(
                pair="ETH/USDT:USDT",
                order_type="limit",
                amount=1.0,
                rate=100.0,
                time_in_force="gtc",
                current_time=datetime.now(timezone.utc),
                entry_tag="trend_pullback",
                side="long",
            )

        assert result is True

    def test_sl_calculated_correctly(self, strategy):
        """SL = rate*(1+stoploss)."""
        last = self._make_last_candle()
        self._setup_dp(strategy, last)
        strategy._db.next_signal_number.return_value = 1

        captured = {}

        def capture_format_entry(*args, **kwargs):
            # format_entry_signal is called positionally; map by position
            # Signature: signal_num, pair, side_str, leverage, setup_name, rate,
            #            sl_price, stoploss_pct, rr_ratio, ...
            if len(args) >= 7:
                captured["sl_price"] = args[6]
            captured.update(kwargs)
            return "msg"

        with (
            patch("TrendRiderStrategy.calc_confidence", return_value=("STRONG", "8/10", [], 8)),
            patch("TrendRiderStrategy.market_context", return_value="ctx"),
            patch("TrendRiderStrategy.get_market_regime", return_value="Trending Bull"),
            patch("TrendRiderStrategy.get_estimated_hold", return_value="2-6h"),
            patch("TrendRiderStrategy.build_detailed_reason", return_value="reason"),
            patch("TrendRiderStrategy.format_entry_signal", side_effect=capture_format_entry),
            patch("TrendRiderStrategy.format_cornix_signal", return_value="cornix"),
        ):
            strategy.confirm_trade_entry(
                pair="ETH/USDT:USDT",
                order_type="limit",
                amount=1.0,
                rate=200.0,  # rate = 200
                time_in_force="gtc",
                current_time=datetime.now(timezone.utc),
                entry_tag="trend_pullback",
                side="long",
            )

        assert abs(captured["sl_price"] - 200.0 * (1 - 0.06)) < 0.01

    def test_setup_name_resolved_from_entry_tag(self, strategy):
        last = self._make_last_candle()
        self._setup_dp(strategy, last)
        strategy._db.next_signal_number.return_value = 1

        captured_name = {}

        def capture(*args, **kwargs):
            # setup_name is the 5th positional arg (index 4)
            if len(args) >= 5:
                captured_name["name"] = args[4]
            else:
                captured_name["name"] = kwargs.get("setup_name")
            return "msg"

        with (
            patch("TrendRiderStrategy.calc_confidence", return_value=("GOOD", "7/10", [], 7)),
            patch("TrendRiderStrategy.market_context", return_value="ctx"),
            patch("TrendRiderStrategy.get_market_regime", return_value="Trending Bull"),
            patch("TrendRiderStrategy.get_estimated_hold", return_value="6-24h"),
            patch("TrendRiderStrategy.build_detailed_reason", return_value="reason"),
            patch("TrendRiderStrategy.format_entry_signal", side_effect=capture),
            patch("TrendRiderStrategy.format_cornix_signal", return_value="cornix"),
        ):
            strategy.confirm_trade_entry(
                pair="ETH/USDT:USDT",
                order_type="limit",
                amount=1.0,
                rate=100.0,
                time_in_force="gtc",
                current_time=datetime.now(timezone.utc),
                entry_tag="ema50_bounce",
                side="long",
            )

        assert captured_name["name"] == "EMA50 Bounce"


# ---------------------------------------------------------------------------
# 6. confirm_trade_exit (formerly custom_exit)
# ---------------------------------------------------------------------------

class TestConfirmTradeExit:
    """Verify confirm_trade_exit: always returns True, sends exit message."""

    def _make_trade(self):
        trade = MagicMock()
        trade.open_rate = 100.0
        trade.pair = "ETH/USDT:USDT"
        trade.open_date_utc = datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc)
        trade.calc_profit_ratio.return_value = 0.05
        return trade

    def test_always_returns_true(self, strategy):
        strategy.dp = MagicMock()
        trade = self._make_trade()

        with (
            patch("TrendRiderStrategy.format_exit_report", return_value="exit_msg"),
            patch("TrendRiderStrategy.get_running_stats", return_value="stats"),
            patch("TrendRiderStrategy.format_exit_footer", return_value=" footer"),
        ):
            result = strategy.confirm_trade_exit(
                pair="ETH/USDT:USDT",
                trade=trade,
                order_type="limit",
                amount=1.0,
                rate=105.0,
                time_in_force="gtc",
                exit_reason="roi",
                current_time=datetime.now(timezone.utc),
            )

        assert result is True

    def test_sends_exit_message_via_dp(self, strategy):
        strategy.dp = MagicMock()
        trade = self._make_trade()

        with (
            patch("TrendRiderStrategy.format_exit_report", return_value="EXIT_REPORT"),
            patch("TrendRiderStrategy.get_running_stats", return_value="STATS"),
            patch("TrendRiderStrategy.format_exit_footer", return_value=" FOOTER"),
        ):
            strategy.confirm_trade_exit(
                pair="ETH/USDT:USDT",
                trade=trade,
                order_type="limit",
                amount=1.0,
                rate=105.0,
                time_in_force="gtc",
                exit_reason="roi",
                current_time=datetime.now(timezone.utc),
            )

        strategy.dp.send_msg.assert_called_once()
        sent_msg = strategy.dp.send_msg.call_args[0][0]
        assert "EXIT_REPORT" in sent_msg
        assert "FOOTER" in sent_msg

    def test_format_exit_report_receives_correct_args(self, strategy):
        strategy.dp = MagicMock()
        trade = self._make_trade()
        rate = 112.0
        reason = "trailing_stop_loss"
        now = datetime(2026, 3, 23, 15, 0, 0, tzinfo=timezone.utc)

        with (
            patch("TrendRiderStrategy.format_exit_report", return_value="msg") as mock_rep,
            patch("TrendRiderStrategy.get_running_stats", return_value=""),
            patch("TrendRiderStrategy.format_exit_footer", return_value=""),
        ):
            strategy.confirm_trade_exit(
                pair="ETH/USDT:USDT",
                trade=trade,
                order_type="limit",
                amount=1.0,
                rate=rate,
                time_in_force="gtc",
                exit_reason=reason,
                current_time=now,
            )

        mock_rep.assert_called_once_with("ETH/USDT:USDT", trade, rate, reason, now)


# ---------------------------------------------------------------------------
# 7. informative_pairs
# ---------------------------------------------------------------------------

class TestInformativePairs:
    def test_returns_list(self, strategy):
        strategy.dp = MagicMock()
        strategy.dp.current_whitelist.return_value = ["ETH/USDT:USDT", "SOL/USDT:USDT"]
        result = strategy.informative_pairs()
        assert isinstance(result, list)

    def test_includes_4h_for_each_pair(self, strategy):
        whitelist = ["ETH/USDT:USDT", "SOL/USDT:USDT"]
        strategy.dp = MagicMock()
        strategy.dp.current_whitelist.return_value = whitelist
        result = strategy.informative_pairs()
        for pair in whitelist:
            assert (pair, "4h") in result, f"Missing 4h for {pair}"

    def test_includes_1d_for_each_pair(self, strategy):
        whitelist = ["ETH/USDT:USDT"]
        strategy.dp = MagicMock()
        strategy.dp.current_whitelist.return_value = whitelist
        result = strategy.informative_pairs()
        assert ("ETH/USDT:USDT", "1d") in result

    def test_includes_btc_1h_sentiment(self, strategy):
        strategy.dp = MagicMock()
        strategy.dp.current_whitelist.return_value = []
        result = strategy.informative_pairs()
        assert ("BTC/USDT:USDT", "1h") in result

    def test_includes_btc_4h_sentiment(self, strategy):
        strategy.dp = MagicMock()
        strategy.dp.current_whitelist.return_value = []
        result = strategy.informative_pairs()
        assert ("BTC/USDT:USDT", "4h") in result

    def test_returns_empty_pairs_when_no_dp(self, strategy):
        strategy.dp = None
        result = strategy.informative_pairs()
        # BTC pairs should still be included
        assert ("BTC/USDT:USDT", "1h") in result
        assert ("BTC/USDT:USDT", "4h") in result

    def test_no_duplicates_for_single_pair(self, strategy):
        strategy.dp = MagicMock()
        strategy.dp.current_whitelist.return_value = ["ETH/USDT:USDT"]
        result = strategy.informative_pairs()
        assert len(result) == len(set(result))

    def test_each_entry_is_tuple_of_two_strings(self, strategy):
        strategy.dp = MagicMock()
        strategy.dp.current_whitelist.return_value = ["ETH/USDT:USDT"]
        result = strategy.informative_pairs()
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], str)


# ---------------------------------------------------------------------------
# 8. leverage
# ---------------------------------------------------------------------------

class TestLeverage:
    def test_returns_leverage_value_by_default(self, strategy):
        result = strategy.leverage(
            pair="ETH/USDT:USDT",
            current_time=datetime.now(timezone.utc),
            current_rate=100.0,
            proposed_leverage=3.0,
            max_leverage=100.0,
            entry_tag="trend_pullback",
            side="long",
        )
        assert result == 3.0

    def test_capped_by_max_leverage(self, strategy):
        """If max_leverage < leverage_value, result is capped at max_leverage."""
        strategy.leverage_value = 5
        result = strategy.leverage(
            pair="ETH/USDT:USDT",
            current_time=datetime.now(timezone.utc),
            current_rate=100.0,
            proposed_leverage=5.0,
            max_leverage=2.0,  # max is lower than desired
            entry_tag="trend_pullback",
            side="long",
        )
        assert result == 2.0

    def test_returns_float(self, strategy):
        result = strategy.leverage(
            pair="BTC/USDT:USDT",
            current_time=datetime.now(timezone.utc),
            current_rate=50000.0,
            proposed_leverage=3.0,
            max_leverage=10.0,
            entry_tag="rsi_bounce",
            side="long",
        )
        assert isinstance(result, float)

    def test_consistent_across_pairs(self, strategy):
        """Leverage should be the same regardless of pair or entry_tag."""
        for pair in ["ETH/USDT:USDT", "SOL/USDT:USDT", "BTC/USDT:USDT"]:
            for tag in ["trend_pullback", "ema50_bounce", "rsi_bounce"]:
                r = strategy.leverage(
                    pair=pair,
                    current_time=datetime.now(timezone.utc),
                    current_rate=100.0,
                    proposed_leverage=3.0,
                    max_leverage=10.0,
                    entry_tag=tag,
                    side="long",
                )
                assert r == float(strategy.leverage_value)

    def test_extra_kwargs_accepted(self, strategy):
        """Must accept arbitrary kwargs (Freqtrade passes extra fields)."""
        result = strategy.leverage(
            pair="ETH/USDT:USDT",
            current_time=datetime.now(timezone.utc),
            current_rate=100.0,
            proposed_leverage=3.0,
            max_leverage=10.0,
            entry_tag="trend_pullback",
            side="long",
            extra_field="ignored",
        )
        assert result == 3.0


# ---------------------------------------------------------------------------
# 9. Strategy-level constants and parameters
# ---------------------------------------------------------------------------

class TestStrategyConstants:
    def test_timeframe_is_1h(self, strategy):
        assert strategy.timeframe == "1h"

    def test_can_short_is_false(self):
        from TrendRiderStrategy import TrendRiderStrategy
        assert TrendRiderStrategy.can_short is False

    def test_stoploss_is_negative(self, strategy):
        assert strategy.stoploss < 0

    def test_stoploss_magnitude_reasonable(self, strategy):
        # Must be between -2% and -20% for crypto strategies
        assert -0.20 <= strategy.stoploss <= -0.02

    def test_trailing_stop_enabled(self):
        from TrendRiderStrategy import TrendRiderStrategy
        assert TrendRiderStrategy.trailing_stop is True

    def test_trailing_stop_positive_offset_greater_than_positive(self):
        from TrendRiderStrategy import TrendRiderStrategy
        assert TrendRiderStrategy.trailing_stop_positive_offset > TrendRiderStrategy.trailing_stop_positive

    def test_leverage_value_default(self):
        from TrendRiderStrategy import TrendRiderStrategy
        assert TrendRiderStrategy.leverage_value == 3

    def test_minimal_roi_has_zero_key(self):
        from TrendRiderStrategy import TrendRiderStrategy
        keys = list(TrendRiderStrategy.minimal_roi.keys())
        assert "0" in keys

    def test_minimal_roi_values_positive(self):
        from TrendRiderStrategy import TrendRiderStrategy
        for k, v in TrendRiderStrategy.minimal_roi.items():
            assert v >= 0, f"ROI at {k} is negative"

    def test_startup_candle_count_sufficient_for_ema200(self):
        from TrendRiderStrategy import TrendRiderStrategy
        assert TrendRiderStrategy.startup_candle_count >= 200
