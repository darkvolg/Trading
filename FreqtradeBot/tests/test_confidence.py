"""Tests for trendrider_confidence — calc_confidence, market_context, regime, hold time."""

from trendrider_confidence import (
    calc_confidence,
    market_context,
    get_market_regime,
    get_estimated_hold,
)


class TestCalcConfidence:
    def test_returns_tuple_of_four(self, mock_last_candle_bullish):
        result = calc_confidence(mock_last_candle_bullish, adx_threshold=20)
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_return_types(self, mock_last_candle_bullish):
        level, bar, details, numeric = calc_confidence(mock_last_candle_bullish, adx_threshold=20)
        assert isinstance(level, str)
        assert isinstance(bar, str)
        assert isinstance(details, list)
        assert isinstance(numeric, int)

    def test_numeric_range(self, mock_last_candle_bullish):
        _, _, _, numeric = calc_confidence(mock_last_candle_bullish, adx_threshold=20)
        assert 1 <= numeric <= 10

    def test_high_confidence_bullish(self, mock_last_candle_bullish):
        """All bullish indicators should produce high confidence (>=7)."""
        _, _, _, numeric = calc_confidence(mock_last_candle_bullish, adx_threshold=20)
        assert numeric >= 7

    def test_low_confidence_bearish(self, mock_last_candle_bearish):
        """All bearish indicators should produce low confidence (<=4)."""
        _, _, _, numeric = calc_confidence(mock_last_candle_bearish, adx_threshold=20)
        assert numeric <= 4

    def test_level_labels(self, mock_last_candle_bullish, mock_last_candle_bearish):
        level_bull, _, _, _ = calc_confidence(mock_last_candle_bullish, adx_threshold=20)
        level_bear, _, _, _ = calc_confidence(mock_last_candle_bearish, adx_threshold=20)
        assert any(label in level_bull for label in ("STRONG", "GOOD", "MEDIUM", "WEAK"))
        assert any(label in level_bear for label in ("STRONG", "GOOD", "MEDIUM", "WEAK"))

    def test_bar_contains_slash_ten(self, mock_last_candle_bullish):
        _, bar, _, _ = calc_confidence(mock_last_candle_bullish, adx_threshold=20)
        assert "/10" in bar

    def test_details_are_strings(self, mock_last_candle_bullish):
        _, _, details, _ = calc_confidence(mock_last_candle_bullish, adx_threshold=20)
        assert len(details) > 0
        for d in details:
            assert isinstance(d, str)

    def test_bullish_details_populated(self, mock_last_candle_bullish):
        """Bullish candle should trigger multiple detail entries."""
        _, _, details, _ = calc_confidence(mock_last_candle_bullish, adx_threshold=20)
        assert len(details) >= 5

    def test_rsi_period_parameter(self, mock_last_candle_bullish):
        """Custom rsi_period should look up the matching key."""
        candle = dict(mock_last_candle_bullish)
        candle["rsi_7"] = 45.0
        _, _, details, _ = calc_confidence(candle, adx_threshold=20, rsi_period=7)
        assert "RSI healthy" in details

    def test_empty_candle_returns_minimum(self):
        """Empty dict should still return valid result with minimum confidence."""
        level, bar, details, numeric = calc_confidence({}, adx_threshold=20)
        assert numeric >= 1
        assert any(label in level for label in ("STRONG", "GOOD", "MEDIUM", "WEAK"))


class TestMarketContext:
    def test_contains_btc(self, mock_last_candle_bullish):
        ctx = market_context(mock_last_candle_bullish)
        assert "BTC:" in ctx

    def test_bullish_context(self, mock_last_candle_bullish):
        ctx = market_context(mock_last_candle_bullish)
        assert "Bullish" in ctx
        assert "Uptrend" in ctx

    def test_bearish_context(self, mock_last_candle_bearish):
        ctx = market_context(mock_last_candle_bearish)
        assert "Bearish" in ctx
        assert "Downtrend" in ctx

    def test_funding_rate_shown(self, mock_last_candle_bullish):
        ctx = market_context(mock_last_candle_bullish)
        assert "Fund:" in ctx

    def test_no_funding_when_zero(self):
        candle = {"btc_rsi_1h": 50, "btc_is_bull_1h": 0, "is_bull_4h": 0, "funding_rate": 0}
        ctx = market_context(candle)
        assert "Fund:" not in ctx

    def test_returns_string(self, mock_last_candle_bullish):
        assert isinstance(market_context(mock_last_candle_bullish), str)


class TestGetMarketRegime:
    def test_ranging_low_adx(self):
        candle = {"adx": 15, "ema_200": 100, "close": 95, "is_bull": 0,
                  "bb_width": 0.05, "bb_width_sma": 0.10}
        assert get_market_regime(candle) == "Ranging"

    def test_ranging_high_vol(self):
        candle = {"adx": 15, "ema_200": 100, "close": 95, "is_bull": 0,
                  "bb_width": 0.20, "bb_width_sma": 0.10}
        assert get_market_regime(candle) == "Ranging (High Vol)"

    def test_trending_bull(self):
        candle = {"adx": 30, "ema_200": 90, "close": 100, "is_bull": 1,
                  "bb_width": 0.10, "bb_width_sma": 0.10}
        assert get_market_regime(candle) == "Trending Bull"

    def test_trending_bear(self):
        candle = {"adx": 30, "ema_200": 110, "close": 100, "is_bull": 0,
                  "bb_width": 0.10, "bb_width_sma": 0.10}
        assert get_market_regime(candle) == "Trending Bear"

    def test_trending_bear_high_vol(self):
        candle = {"adx": 30, "ema_200": 110, "close": 100, "is_bull": 0,
                  "bb_width": 0.20, "bb_width_sma": 0.10}
        assert get_market_regime(candle) == "Trending Bear (High Vol)"

    def test_valid_regime_strings(self, mock_last_candle_bullish):
        regime = get_market_regime(mock_last_candle_bullish)
        valid = {"Ranging", "Ranging (High Vol)", "Trending Bull",
                 "Trending Bear", "Trending Bear (High Vol)"}
        assert regime in valid


class TestGetEstimatedHold:
    def test_high_confidence(self):
        assert get_estimated_hold(8) == "2-6h"
        assert get_estimated_hold(9) == "2-6h"
        assert get_estimated_hold(10) == "2-6h"

    def test_medium_confidence(self):
        assert get_estimated_hold(6) == "6-24h"
        assert get_estimated_hold(7) == "6-24h"

    def test_low_confidence(self):
        assert get_estimated_hold(5) == "24-48h"
        assert get_estimated_hold(3) == "24-48h"
        assert get_estimated_hold(1) == "24-48h"
