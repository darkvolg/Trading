"""Shared fixtures for TrendRider integration tests."""

import sys
from pathlib import Path

import pytest

# Add strategies directory to sys.path so we can import the modules directly
STRATEGIES_DIR = str(Path(__file__).resolve().parent.parent / "user_data" / "strategies")
if STRATEGIES_DIR not in sys.path:
    sys.path.insert(0, STRATEGIES_DIR)


@pytest.fixture
def mock_last_candle_bullish() -> dict:
    """Realistic candle data with all indicators in a bullish scenario."""
    return {
        "close": 100.0,
        "rsi_14": 45.0,
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


@pytest.fixture
def mock_last_candle_bearish() -> dict:
    """Realistic candle data with all indicators in a bearish scenario."""
    return {
        "close": 100.0,
        "rsi_14": 70.0,
        "adx": 12.0,
        "volume_ratio": 0.5,
        "macdhist": -0.005,
        "macdhist_prev": -0.003,
        "obv": 1200.0,
        "obv_ema": 1400.0,
        "btc_rsi_1h": 30.0,
        "btc_is_bull_1h": 0,
        "is_bull_4h": 0,
        "adx_4h": 15.0,
        "bb_lower": 95.0,
        "bb_upper": 110.0,
        "bb_width": 0.08,
        "bb_width_sma": 0.10,
        "plus_di": 15.0,
        "minus_di": 30.0,
        "fng_value": 20,
        "funding_rate": 0.0005,
        "ema_200": 110.0,
        "ema_50": 105.0,
        "ema_20": 102.0,
        "ema_9": 101.0,
        "is_bull": 0,
    }


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a temporary database config pointing at tmp_path."""
    return {"user_data_dir": tmp_path}
