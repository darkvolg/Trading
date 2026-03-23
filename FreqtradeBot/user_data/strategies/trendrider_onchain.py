"""
TrendRider On-Chain — Bybit API (funding rate, open interest) and Fear & Greed Index.
"""

import json
import os
import time
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path

from trendrider_config import FNG_CACHE_TTL, FUNDING_EXTREME_THRESHOLD

logger = logging.getLogger(__name__)


class FearGreedFetcher:
    """Fetches and caches Fear & Greed Index from alternative.me API."""

    def __init__(self, config: dict):
        data_dir = config.get('user_data_dir', Path('.'))
        if isinstance(data_dir, str):
            data_dir = Path(data_dir)
        self.cache_file = str(data_dir / 'fng_cache.json')
        self.cache_ttl = FNG_CACHE_TTL

    def fetch(self) -> dict:
        """Fetch FNG data with file-based cache. Returns {date_str: value}."""
        # Check cache
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cached = json.load(f)
                cached_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
                if cached_time.tzinfo is None:
                    cached_time = cached_time.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - cached_time).total_seconds() < self.cache_ttl:
                    return cached.get('data', {})
            except Exception:
                pass

        # Fetch fresh data
        try:
            resp = requests.get(
                'https://api.alternative.me/fng/?limit=60&format=json',
                timeout=10
            )
            resp.raise_for_status()
            raw = resp.json()
            data_list = raw.get('data', [])
            fng_map = {}
            for item in data_list:
                ts = int(item.get('timestamp', 0))
                val = int(item.get('value', 50))
                date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d')
                fng_map[date_str] = val

            # Save cache
            if self.cache_file:
                try:
                    with open(self.cache_file, 'w') as f:
                        json.dump({
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'data': fng_map
                        }, f)
                except Exception:
                    pass
            return fng_map
        except Exception as e:
            logger.warning(f"FNG fetch failed: {e}")
            return {}


class OnChainDataFetcher:
    """Fetches funding rate and open interest from Bybit v5 API with caching."""

    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self._cache = {}  # {pair: {'rate': float, 'oi_change': float, 'ts': float}}

    @property
    def cache(self) -> dict:
        return self._cache

    @staticmethod
    def pair_to_bybit_symbol(pair: str) -> str:
        """Convert Freqtrade pair format to Bybit symbol. E.g. 'BTC/USDT:USDT' -> 'BTCUSDT'."""
        return pair.replace('/USDT:USDT', 'USDT').replace('/', '')

    def fetch_funding_rate(self, pair: str) -> float:
        """Fetch latest funding rate with cache."""
        cached = self._cache.get(pair, {})
        if cached and (time.time() - cached.get('ts', 0)) < self.cache_ttl:
            return cached.get('rate', 0.0)

        symbol = self.pair_to_bybit_symbol(pair)
        try:
            resp = requests.get(
                'https://api.bybit.com/v5/market/funding/history',
                params={'category': 'linear', 'symbol': symbol, 'limit': 1},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            result_list = data.get('result', {}).get('list', [])
            rate = float(result_list[0].get('fundingRate', 0)) if result_list else 0.0
        except Exception as e:
            logger.warning(f"Funding rate fetch failed for {pair}: {e}")
            rate = cached.get('rate', 0.0)

        # Update cache (preserve oi_change if already fetched)
        existing = self._cache.get(pair, {})
        self._cache[pair] = {
            'rate': rate,
            'oi_change': existing.get('oi_change', 0.0),
            'ts': time.time(),
        }
        return rate

    def fetch_open_interest(self, pair: str) -> float:
        """Fetch open interest change ratio with cache."""
        cached = self._cache.get(pair, {})
        if cached and (time.time() - cached.get('ts', 0)) < self.cache_ttl:
            return cached.get('oi_change', 0.0)

        symbol = self.pair_to_bybit_symbol(pair)
        try:
            resp = requests.get(
                'https://api.bybit.com/v5/market/open-interest',
                params={'category': 'linear', 'symbol': symbol, 'intervalTime': '1h', 'limit': 2},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            result_list = data.get('result', {}).get('list', [])
            if len(result_list) >= 2:
                current_oi = float(result_list[0].get('openInterest', 0))
                previous_oi = float(result_list[1].get('openInterest', 0))
                oi_change = (current_oi / previous_oi) - 1 if previous_oi > 0 else 0.0
            else:
                oi_change = 0.0
        except Exception as e:
            logger.warning(f"Open interest fetch failed for {pair}: {e}")
            oi_change = cached.get('oi_change', 0.0)

        # Update cache (preserve rate if already fetched)
        existing = self._cache.get(pair, {})
        self._cache[pair] = {
            'rate': existing.get('rate', 0.0),
            'oi_change': oi_change,
            'ts': time.time(),
        }
        return oi_change

    def is_funding_extreme(self, pair: str) -> bool:
        """Check if funding rate is extreme for a given pair."""
        rate = self._cache.get(pair, {}).get('rate', 0.0)
        return abs(rate) > FUNDING_EXTREME_THRESHOLD
