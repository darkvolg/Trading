"""Tests for trendrider_config — verify all constants are defined with correct types/ranges."""

import trendrider_config as cfg


class TestFngThresholds:
    def test_fng_healthy_range(self):
        assert cfg.FNG_HEALTHY_MIN < cfg.FNG_HEALTHY_MAX

    def test_fng_neutral_range(self):
        assert cfg.FNG_NEUTRAL_MIN < cfg.FNG_NEUTRAL_MAX

    def test_fng_values_are_ints(self):
        for val in (cfg.FNG_HEALTHY_MIN, cfg.FNG_HEALTHY_MAX,
                    cfg.FNG_NEUTRAL_MIN, cfg.FNG_NEUTRAL_MAX):
            assert isinstance(val, int)

    def test_fng_cache_ttl_positive(self):
        assert cfg.FNG_CACHE_TTL > 0


class TestTakeProfitLevels:
    def test_tp_percentages_are_positive_floats(self):
        for tp in (cfg.TP1_PCT, cfg.TP2_PCT, cfg.TP3_PCT):
            assert isinstance(tp, float)
            assert tp > 0

    def test_tp_ordering(self):
        assert cfg.TP1_PCT < cfg.TP2_PCT < cfg.TP3_PCT


class TestConfidenceConstants:
    def test_confidence_max_score_positive(self):
        assert cfg.CONFIDENCE_MAX_SCORE > 0

    def test_confidence_min_values_in_range(self):
        for val in (cfg.CONFIDENCE_MIN_DEFAULT, cfg.CONFIDENCE_MIN_BEAR):
            assert isinstance(val, int)
            assert 1 <= val <= 10


class TestEstHoldMap:
    def test_keys_are_ints(self):
        for key in cfg.EST_HOLD_MAP:
            assert isinstance(key, int)

    def test_values_are_strings(self):
        for val in cfg.EST_HOLD_MAP.values():
            assert isinstance(val, str)
            assert len(val) > 0

    def test_has_expected_keys(self):
        assert 8 in cfg.EST_HOLD_MAP
        assert 6 in cfg.EST_HOLD_MAP
        assert 0 in cfg.EST_HOLD_MAP


class TestSetupNames:
    def test_keys_and_values_are_strings(self):
        for key, val in cfg.SETUP_NAMES.items():
            assert isinstance(key, str)
            assert isinstance(val, str)

    def test_has_known_setups(self):
        assert "trend_pullback" in cfg.SETUP_NAMES
        assert "ema50_bounce" in cfg.SETUP_NAMES
        assert "rsi_bounce" in cfg.SETUP_NAMES


class TestExitReasons:
    def test_exit_reasons_are_strings(self):
        for key, val in cfg.EXIT_REASONS.items():
            assert isinstance(key, str)
            assert isinstance(val, str)

    def test_has_standard_reasons(self):
        assert "roi" in cfg.EXIT_REASONS
        assert "stop_loss" in cfg.EXIT_REASONS
        assert "trailing_stop_loss" in cfg.EXIT_REASONS



class TestEntryZone:
    def test_entry_zone_positive(self):
        assert cfg.ENTRY_ZONE_PCT > 0
        assert isinstance(cfg.ENTRY_ZONE_PCT, float)
