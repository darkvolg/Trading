"""Tests for trendrider_onchain — FearGreedFetcher and OnChainDataFetcher."""

import json
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from trendrider_onchain import FearGreedFetcher, OnChainDataFetcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fng_api_response(entries=None):
    """Build a realistic alternative.me FNG API response dict."""
    if entries is None:
        entries = [
            {"timestamp": "1711152000", "value": "72", "value_classification": "Greed"},
            {"timestamp": "1711065600", "value": "65", "value_classification": "Greed"},
            {"timestamp": "1710979200", "value": "58", "value_classification": "Greed"},
        ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": entries}
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def _bybit_funding_response(rate="0.0001"):
    """Build a realistic Bybit funding-rate API response."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "retCode": 0,
        "result": {
            "list": [{"fundingRate": rate, "fundingRateTimestamp": "1711152000000"}]
        },
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def _bybit_oi_response(current="1000000", previous="900000"):
    """Build a realistic Bybit open-interest API response with 2 entries."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {"openInterest": current, "timestamp": "1711152000000"},
                {"openInterest": previous, "timestamp": "1711148400000"},
            ]
        },
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


# ---------------------------------------------------------------------------
# FearGreedFetcher — construction
# ---------------------------------------------------------------------------

class TestFearGreedFetcherInit:
    def test_cache_file_uses_config_dir(self, tmp_path):
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        assert fetcher.cache_file == str(tmp_path / "fng_cache.json")

    def test_cache_file_accepts_string_path(self, tmp_path):
        fetcher = FearGreedFetcher({"user_data_dir": str(tmp_path)})
        assert fetcher.cache_file == str(tmp_path / "fng_cache.json")

    def test_cache_file_falls_back_to_dot(self):
        fetcher = FearGreedFetcher({})
        assert fetcher.cache_file.endswith("fng_cache.json")

    def test_cache_ttl_from_config(self, tmp_path):
        """FNG_CACHE_TTL from trendrider_config must be positive."""
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        assert fetcher.cache_ttl > 0


# ---------------------------------------------------------------------------
# FearGreedFetcher — success path (no cache)
# ---------------------------------------------------------------------------

class TestFearGreedFetcherSuccess:
    @patch("trendrider_onchain.requests.get")
    def test_returns_dict_on_success(self, mock_get, tmp_path):
        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        assert isinstance(result, dict)

    @patch("trendrider_onchain.requests.get")
    def test_keys_are_date_strings(self, mock_get, tmp_path):
        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        for key in result:
            # Must parse as YYYY-MM-DD
            datetime.strptime(key, "%Y-%m-%d")

    @patch("trendrider_onchain.requests.get")
    def test_values_are_ints(self, mock_get, tmp_path):
        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        for val in result.values():
            assert isinstance(val, int)

    @patch("trendrider_onchain.requests.get")
    def test_correct_values_parsed(self, mock_get, tmp_path):
        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        # timestamp 1711152000 → 2024-03-23
        assert result.get("2024-03-23") == 72

    @patch("trendrider_onchain.requests.get")
    def test_cache_file_written_after_fetch(self, mock_get, tmp_path):
        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        fetcher.fetch()
        assert (tmp_path / "fng_cache.json").exists()

    @patch("trendrider_onchain.requests.get")
    def test_cache_file_contains_timestamp_and_data(self, mock_get, tmp_path):
        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        fetcher.fetch()
        with open(tmp_path / "fng_cache.json") as f:
            stored = json.load(f)
        assert "timestamp" in stored
        assert "data" in stored
        assert isinstance(stored["data"], dict)

    @patch("trendrider_onchain.requests.get")
    def test_empty_data_list_returns_empty_dict(self, mock_get, tmp_path):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        assert result == {}

    @patch("trendrider_onchain.requests.get")
    def test_missing_value_field_defaults_to_50(self, mock_get, tmp_path):
        entries = [{"timestamp": "1711152000"}]  # no 'value' key
        mock_get.return_value = _fng_api_response(entries)
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        assert result.get("2024-03-23") == 50


# ---------------------------------------------------------------------------
# FearGreedFetcher — API failure
# ---------------------------------------------------------------------------

class TestFearGreedFetcherAPIFailure:
    @patch("trendrider_onchain.requests.get", side_effect=requests.ConnectionError("timeout"))
    def test_connection_error_returns_empty_dict(self, mock_get, tmp_path):
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        assert result == {}

    @patch("trendrider_onchain.requests.get")
    def test_http_error_returns_empty_dict(self, mock_get, tmp_path):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("503 Service Unavailable")
        mock_get.return_value = mock_resp
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        assert result == {}

    @patch("trendrider_onchain.requests.get")
    def test_json_parse_error_returns_empty_dict(self, mock_get, tmp_path):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = ValueError("Not valid JSON")
        mock_get.return_value = mock_resp
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        assert result == {}

    @patch("trendrider_onchain.requests.get")
    def test_missing_data_key_returns_empty_dict(self, mock_get, tmp_path):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {}  # no 'data' key
        mock_get.return_value = mock_resp
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        assert result == {}

    @patch("trendrider_onchain.requests.get", side_effect=requests.Timeout("timed out"))
    def test_timeout_returns_empty_dict(self, mock_get, tmp_path):
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()
        assert result == {}


# ---------------------------------------------------------------------------
# FearGreedFetcher — caching behaviour
# ---------------------------------------------------------------------------

class TestFearGreedFetcherCache:
    @patch("trendrider_onchain.requests.get")
    def test_fresh_cache_prevents_api_call(self, mock_get, tmp_path):
        """If cache is fresh, no HTTP request should be made."""
        cache_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"2024-03-23": 72},
        }
        with open(tmp_path / "fng_cache.json", "w") as f:
            json.dump(cache_data, f)

        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        result = fetcher.fetch()

        mock_get.assert_not_called()
        assert result == {"2024-03-23": 72}

    @patch("trendrider_onchain.requests.get")
    def test_stale_cache_triggers_api_call(self, mock_get, tmp_path):
        """Expired cache should cause a fresh HTTP request."""
        # Write a cache that is older than FNG_CACHE_TTL
        stale_ts = "2000-01-01T00:00:00+00:00"
        cache_data = {"timestamp": stale_ts, "data": {"2000-01-01": 30}}
        with open(tmp_path / "fng_cache.json", "w") as f:
            json.dump(cache_data, f)

        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        fetcher.fetch()

        mock_get.assert_called_once()

    @patch("trendrider_onchain.requests.get")
    def test_corrupt_cache_falls_through_to_api(self, mock_get, tmp_path):
        """Corrupted cache JSON should be ignored and API should be called."""
        with open(tmp_path / "fng_cache.json", "w") as f:
            f.write("NOT JSON {{{")

        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        fetcher.fetch()

        mock_get.assert_called_once()

    @patch("trendrider_onchain.requests.get")
    def test_cache_miss_when_no_file(self, mock_get, tmp_path):
        """No cache file present — must go to API."""
        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        fetcher.fetch()

        mock_get.assert_called_once()

    @patch("trendrider_onchain.requests.get")
    def test_cache_write_failure_does_not_raise(self, mock_get, tmp_path):
        """If writing the cache file fails, fetch() must still return data."""
        mock_get.return_value = _fng_api_response()
        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        # Point cache_file to a directory to trigger write error
        fetcher.cache_file = str(tmp_path)  # can't write to a directory
        result = fetcher.fetch()
        assert isinstance(result, dict)

    @patch("trendrider_onchain.requests.get")
    def test_naive_datetime_in_cache_is_handled(self, mock_get, tmp_path):
        """Cache timestamp without timezone info should not blow up."""
        cache_data = {
            "timestamp": datetime.now().isoformat(),  # naive, no tz
            "data": {"2024-03-23": 55},
        }
        with open(tmp_path / "fng_cache.json", "w") as f:
            json.dump(cache_data, f)

        fetcher = FearGreedFetcher({"user_data_dir": tmp_path})
        # Should not raise; outcome depends on age but must return a dict
        result = fetcher.fetch()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# OnChainDataFetcher — construction
# ---------------------------------------------------------------------------

class TestOnChainDataFetcherInit:
    def test_default_cache_ttl(self):
        fetcher = OnChainDataFetcher()
        assert fetcher.cache_ttl == 300

    def test_custom_cache_ttl(self):
        fetcher = OnChainDataFetcher(cache_ttl=600)
        assert fetcher.cache_ttl == 600

    def test_cache_starts_empty(self):
        fetcher = OnChainDataFetcher()
        assert fetcher.cache == {}


# ---------------------------------------------------------------------------
# OnChainDataFetcher — pair_to_bybit_symbol
# ---------------------------------------------------------------------------

class TestPairToBybitSymbol:
    def test_standard_perpetual(self):
        assert OnChainDataFetcher.pair_to_bybit_symbol("BTC/USDT:USDT") == "BTCUSDT"

    def test_eth_perpetual(self):
        assert OnChainDataFetcher.pair_to_bybit_symbol("ETH/USDT:USDT") == "ETHUSDT"

    def test_doge_perpetual(self):
        assert OnChainDataFetcher.pair_to_bybit_symbol("DOGE/USDT:USDT") == "DOGEUSDT"

    def test_spot_pair(self):
        # 'SOL/USDT' has no ':USDT' — replace('/','') gives 'SOLUSDT'
        result = OnChainDataFetcher.pair_to_bybit_symbol("SOL/USDT")
        assert "SOL" in result
        assert "/" not in result


# ---------------------------------------------------------------------------
# fetch_funding_rate — success path
# ---------------------------------------------------------------------------

class TestFetchFundingRateSuccess:
    @patch("trendrider_onchain.requests.get")
    def test_returns_float(self, mock_get):
        mock_get.return_value = _bybit_funding_response("0.0001")
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert isinstance(rate, float)

    @patch("trendrider_onchain.requests.get")
    def test_correct_value_parsed(self, mock_get):
        mock_get.return_value = _bybit_funding_response("0.0001")
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert rate == pytest.approx(0.0001)

    @patch("trendrider_onchain.requests.get")
    def test_negative_rate(self, mock_get):
        mock_get.return_value = _bybit_funding_response("-0.0003")
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("ETH/USDT:USDT")
        assert rate == pytest.approx(-0.0003)

    @patch("trendrider_onchain.requests.get")
    def test_zero_rate(self, mock_get):
        mock_get.return_value = _bybit_funding_response("0.0")
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert rate == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get")
    def test_very_small_positive_rate(self, mock_get):
        mock_get.return_value = _bybit_funding_response("0.000001")
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert rate == pytest.approx(0.000001)

    @patch("trendrider_onchain.requests.get")
    def test_rate_stored_in_cache(self, mock_get):
        mock_get.return_value = _bybit_funding_response("0.0002")
        fetcher = OnChainDataFetcher()
        fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert "BTC/USDT:USDT" in fetcher.cache
        assert fetcher.cache["BTC/USDT:USDT"]["rate"] == pytest.approx(0.0002)

    @patch("trendrider_onchain.requests.get")
    def test_empty_list_returns_zero(self, mock_get):
        """Empty result list should default to 0.0."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"retCode": 0, "result": {"list": []}}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert rate == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get")
    def test_correct_bybit_endpoint_called(self, mock_get):
        mock_get.return_value = _bybit_funding_response()
        fetcher = OnChainDataFetcher()
        fetcher.fetch_funding_rate("BTC/USDT:USDT")
        call_url = mock_get.call_args[0][0]
        assert "bybit.com" in call_url
        assert "funding" in call_url

    @patch("trendrider_onchain.requests.get")
    def test_symbol_passed_in_params(self, mock_get):
        mock_get.return_value = _bybit_funding_response()
        fetcher = OnChainDataFetcher()
        fetcher.fetch_funding_rate("ETH/USDT:USDT")
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["symbol"] == "ETHUSDT"


# ---------------------------------------------------------------------------
# fetch_funding_rate — API failure
# ---------------------------------------------------------------------------

class TestFetchFundingRateFailure:
    @patch("trendrider_onchain.requests.get", side_effect=requests.ConnectionError)
    def test_connection_error_returns_zero_when_no_cache(self, mock_get):
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert rate == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get")
    def test_http_error_returns_cached_value(self, mock_get):
        """On HTTP error, last cached rate must be returned."""
        fetcher = OnChainDataFetcher()
        # Pre-seed stale cache with a known rate
        fetcher._cache["BTC/USDT:USDT"] = {"rate": 0.00025, "oi_change": 0.0, "ts": 0}

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500")
        mock_get.return_value = mock_resp

        rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert rate == pytest.approx(0.00025)

    @patch("trendrider_onchain.requests.get")
    def test_json_decode_error_returns_zero_no_cache(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = ValueError("bad json")
        mock_get.return_value = mock_resp
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert rate == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get", side_effect=requests.Timeout)
    def test_timeout_returns_zero_no_cache(self, mock_get):
        fetcher = OnChainDataFetcher()
        rate = fetcher.fetch_funding_rate("ETH/USDT:USDT")
        assert rate == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# fetch_funding_rate — caching behaviour
# ---------------------------------------------------------------------------

class TestFetchFundingRateCache:
    @patch("trendrider_onchain.requests.get")
    def test_fresh_cache_prevents_api_call(self, mock_get):
        fetcher = OnChainDataFetcher(cache_ttl=300)
        fetcher._cache["BTC/USDT:USDT"] = {
            "rate": 0.0001,
            "oi_change": 0.0,
            "ts": time.time(),  # fresh timestamp
        }
        result = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        mock_get.assert_not_called()
        assert result == pytest.approx(0.0001)

    @patch("trendrider_onchain.requests.get")
    def test_stale_cache_triggers_api_call(self, mock_get):
        mock_get.return_value = _bybit_funding_response("0.0002")
        fetcher = OnChainDataFetcher(cache_ttl=300)
        fetcher._cache["BTC/USDT:USDT"] = {
            "rate": 0.0001,
            "oi_change": 0.0,
            "ts": 0,  # epoch — definitely stale
        }
        result = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        mock_get.assert_called_once()
        assert result == pytest.approx(0.0002)

    @patch("trendrider_onchain.requests.get")
    def test_oi_change_preserved_on_rate_update(self, mock_get):
        """Updating rate must not wipe out oi_change in cache."""
        mock_get.return_value = _bybit_funding_response("0.0003")
        fetcher = OnChainDataFetcher(cache_ttl=300)
        fetcher._cache["BTC/USDT:USDT"] = {
            "rate": 0.0,
            "oi_change": 0.05,
            "ts": 0,  # stale
        }
        fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert fetcher.cache["BTC/USDT:USDT"]["oi_change"] == pytest.approx(0.05)

    @patch("trendrider_onchain.requests.get")
    def test_cache_ts_updated_after_fetch(self, mock_get):
        mock_get.return_value = _bybit_funding_response("0.0001")
        fetcher = OnChainDataFetcher()
        before = time.time()
        fetcher.fetch_funding_rate("BTC/USDT:USDT")
        after = time.time()
        ts = fetcher.cache["BTC/USDT:USDT"]["ts"]
        assert before <= ts <= after


# ---------------------------------------------------------------------------
# fetch_open_interest — success path
# ---------------------------------------------------------------------------

class TestFetchOpenInterestSuccess:
    @patch("trendrider_onchain.requests.get")
    def test_returns_float(self, mock_get):
        mock_get.return_value = _bybit_oi_response("1000000", "900000")
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert isinstance(oi, float)

    @patch("trendrider_onchain.requests.get")
    def test_correct_change_ratio(self, mock_get):
        # (1_000_000 / 900_000) - 1 ≈ 0.1111
        mock_get.return_value = _bybit_oi_response("1000000", "900000")
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(1_000_000 / 900_000 - 1, rel=1e-4)

    @patch("trendrider_onchain.requests.get")
    def test_decrease_is_negative(self, mock_get):
        mock_get.return_value = _bybit_oi_response("800000", "1000000")
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi < 0

    @patch("trendrider_onchain.requests.get")
    def test_no_change_returns_zero(self, mock_get):
        mock_get.return_value = _bybit_oi_response("1000000", "1000000")
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get")
    def test_large_numbers(self, mock_get):
        """OI in billions should not overflow or lose precision."""
        mock_get.return_value = _bybit_oi_response("5000000000", "4500000000")
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(5_000_000_000 / 4_500_000_000 - 1, rel=1e-4)

    @patch("trendrider_onchain.requests.get")
    def test_only_one_entry_returns_zero(self, mock_get):
        """A single entry (no previous) should return 0.0."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "retCode": 0,
            "result": {"list": [{"openInterest": "1000000", "timestamp": "1711152000000"}]},
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get")
    def test_empty_list_returns_zero(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"retCode": 0, "result": {"list": []}}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get")
    def test_previous_oi_zero_returns_zero(self, mock_get):
        """Avoid division by zero when previous OI is 0."""
        mock_get.return_value = _bybit_oi_response("1000000", "0")
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get")
    def test_oi_stored_in_cache(self, mock_get):
        mock_get.return_value = _bybit_oi_response("1000000", "900000")
        fetcher = OnChainDataFetcher()
        fetcher.fetch_open_interest("BTC/USDT:USDT")
        expected = 1_000_000 / 900_000 - 1
        assert fetcher.cache["BTC/USDT:USDT"]["oi_change"] == pytest.approx(expected, rel=1e-4)

    @patch("trendrider_onchain.requests.get")
    def test_correct_bybit_endpoint_called(self, mock_get):
        mock_get.return_value = _bybit_oi_response()
        fetcher = OnChainDataFetcher()
        fetcher.fetch_open_interest("BTC/USDT:USDT")
        call_url = mock_get.call_args[0][0]
        assert "bybit.com" in call_url
        assert "open-interest" in call_url

    @patch("trendrider_onchain.requests.get")
    def test_symbol_passed_in_params(self, mock_get):
        mock_get.return_value = _bybit_oi_response()
        fetcher = OnChainDataFetcher()
        fetcher.fetch_open_interest("ETH/USDT:USDT")
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["symbol"] == "ETHUSDT"


# ---------------------------------------------------------------------------
# fetch_open_interest — API failure
# ---------------------------------------------------------------------------

class TestFetchOpenInterestFailure:
    @patch("trendrider_onchain.requests.get", side_effect=requests.ConnectionError)
    def test_connection_error_returns_zero_no_cache(self, mock_get):
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get")
    def test_http_error_returns_cached_oi(self, mock_get):
        fetcher = OnChainDataFetcher()
        fetcher._cache["BTC/USDT:USDT"] = {"rate": 0.0, "oi_change": 0.08, "ts": 0}

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("503")
        mock_get.return_value = mock_resp

        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(0.08)

    @patch("trendrider_onchain.requests.get")
    def test_json_decode_error_returns_zero_no_cache(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = ValueError("bad json")
        mock_get.return_value = mock_resp
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(0.0)

    @patch("trendrider_onchain.requests.get", side_effect=requests.Timeout)
    def test_timeout_returns_zero(self, mock_get):
        fetcher = OnChainDataFetcher()
        oi = fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert oi == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# fetch_open_interest — caching behaviour
# ---------------------------------------------------------------------------

class TestFetchOpenInterestCache:
    @patch("trendrider_onchain.requests.get")
    def test_fresh_cache_prevents_api_call(self, mock_get):
        fetcher = OnChainDataFetcher(cache_ttl=300)
        fetcher._cache["ETH/USDT:USDT"] = {
            "rate": 0.0,
            "oi_change": 0.05,
            "ts": time.time(),
        }
        result = fetcher.fetch_open_interest("ETH/USDT:USDT")
        mock_get.assert_not_called()
        assert result == pytest.approx(0.05)

    @patch("trendrider_onchain.requests.get")
    def test_stale_cache_triggers_api_call(self, mock_get):
        mock_get.return_value = _bybit_oi_response("1000000", "900000")
        fetcher = OnChainDataFetcher(cache_ttl=300)
        fetcher._cache["ETH/USDT:USDT"] = {"rate": 0.0, "oi_change": 0.01, "ts": 0}
        fetcher.fetch_open_interest("ETH/USDT:USDT")
        mock_get.assert_called_once()

    @patch("trendrider_onchain.requests.get")
    def test_rate_preserved_on_oi_update(self, mock_get):
        """Updating oi_change must not wipe out rate in cache."""
        mock_get.return_value = _bybit_oi_response("1000000", "900000")
        fetcher = OnChainDataFetcher(cache_ttl=300)
        fetcher._cache["BTC/USDT:USDT"] = {"rate": 0.0002, "oi_change": 0.0, "ts": 0}
        fetcher.fetch_open_interest("BTC/USDT:USDT")
        assert fetcher.cache["BTC/USDT:USDT"]["rate"] == pytest.approx(0.0002)


# ---------------------------------------------------------------------------
# is_funding_extreme
# ---------------------------------------------------------------------------

class TestIsFundingExtreme:
    def test_not_extreme_when_cache_empty(self):
        fetcher = OnChainDataFetcher()
        assert fetcher.is_funding_extreme("BTC/USDT:USDT") is False

    def test_extreme_positive_rate(self):
        fetcher = OnChainDataFetcher()
        # FUNDING_EXTREME_THRESHOLD = 0.0003; use a value above it
        fetcher._cache["BTC/USDT:USDT"] = {"rate": 0.0005, "oi_change": 0.0, "ts": time.time()}
        assert fetcher.is_funding_extreme("BTC/USDT:USDT") is True

    def test_extreme_negative_rate(self):
        fetcher = OnChainDataFetcher()
        fetcher._cache["BTC/USDT:USDT"] = {"rate": -0.0005, "oi_change": 0.0, "ts": time.time()}
        assert fetcher.is_funding_extreme("BTC/USDT:USDT") is True

    def test_not_extreme_small_positive(self):
        fetcher = OnChainDataFetcher()
        fetcher._cache["BTC/USDT:USDT"] = {"rate": 0.0001, "oi_change": 0.0, "ts": time.time()}
        assert fetcher.is_funding_extreme("BTC/USDT:USDT") is False

    def test_not_extreme_at_zero(self):
        fetcher = OnChainDataFetcher()
        fetcher._cache["BTC/USDT:USDT"] = {"rate": 0.0, "oi_change": 0.0, "ts": time.time()}
        assert fetcher.is_funding_extreme("BTC/USDT:USDT") is False

    def test_exactly_at_threshold_is_not_extreme(self):
        """abs(rate) > threshold, so the threshold value itself is NOT extreme."""
        from trendrider_config import FUNDING_EXTREME_THRESHOLD
        fetcher = OnChainDataFetcher()
        fetcher._cache["BTC/USDT:USDT"] = {
            "rate": FUNDING_EXTREME_THRESHOLD,
            "oi_change": 0.0,
            "ts": time.time(),
        }
        assert fetcher.is_funding_extreme("BTC/USDT:USDT") is False

    def test_just_above_threshold_is_extreme(self):
        from trendrider_config import FUNDING_EXTREME_THRESHOLD
        fetcher = OnChainDataFetcher()
        fetcher._cache["BTC/USDT:USDT"] = {
            "rate": FUNDING_EXTREME_THRESHOLD + 0.000001,
            "oi_change": 0.0,
            "ts": time.time(),
        }
        assert fetcher.is_funding_extreme("BTC/USDT:USDT") is True

    def test_different_pairs_are_independent(self):
        fetcher = OnChainDataFetcher()
        fetcher._cache["BTC/USDT:USDT"] = {"rate": 0.0005, "oi_change": 0.0, "ts": time.time()}
        fetcher._cache["ETH/USDT:USDT"] = {"rate": 0.0001, "oi_change": 0.0, "ts": time.time()}
        assert fetcher.is_funding_extreme("BTC/USDT:USDT") is True
        assert fetcher.is_funding_extreme("ETH/USDT:USDT") is False


# ---------------------------------------------------------------------------
# Integration: multiple pairs, independent cache slots
# ---------------------------------------------------------------------------

class TestMultiplePairs:
    @patch("trendrider_onchain.requests.get")
    def test_different_pairs_cached_independently(self, mock_get):
        mock_get.side_effect = [
            _bybit_funding_response("0.0001"),
            _bybit_funding_response("0.0005"),
        ]
        fetcher = OnChainDataFetcher()
        btc_rate = fetcher.fetch_funding_rate("BTC/USDT:USDT")
        eth_rate = fetcher.fetch_funding_rate("ETH/USDT:USDT")
        assert btc_rate == pytest.approx(0.0001)
        assert eth_rate == pytest.approx(0.0005)
        assert "BTC/USDT:USDT" in fetcher.cache
        assert "ETH/USDT:USDT" in fetcher.cache

    @patch("trendrider_onchain.requests.get")
    def test_rate_and_oi_coexist_for_same_pair(self, mock_get):
        """Fetch rate, then OI with a stale cache so both API calls fire.

        fetch_funding_rate writes a fresh ts; fetch_open_interest sees that
        fresh ts and skips the API call (cache hit). To force the OI call we
        must reset ts to 0 between the two fetches. After both fetches the
        rate written by the first call must survive alongside oi_change = 0
        (which is what the fresh-cache hit returns from the slot written by
        fetch_funding_rate).
        """
        mock_get.return_value = _bybit_funding_response("0.0002")
        fetcher = OnChainDataFetcher()

        # First call: populate rate via API
        fetcher.fetch_funding_rate("BTC/USDT:USDT")
        assert fetcher.cache["BTC/USDT:USDT"]["rate"] == pytest.approx(0.0002)

        # Expire the cache so the OI call actually hits the API
        fetcher._cache["BTC/USDT:USDT"]["ts"] = 0
        mock_get.return_value = _bybit_oi_response("1000000", "900000")
        fetcher.fetch_open_interest("BTC/USDT:USDT")

        slot = fetcher.cache["BTC/USDT:USDT"]
        # Rate written by fetch_funding_rate must be preserved
        assert slot["rate"] == pytest.approx(0.0002)
        # OI change just returned by the second API call
        assert slot["oi_change"] == pytest.approx(1_000_000 / 900_000 - 1, rel=1e-4)
