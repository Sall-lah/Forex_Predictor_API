"""KrakenRepository wrapping KrakenProvider with caching."""

import time
from typing import Any

from app.core.base import BaseRepository
from app.shared.ohlcv.base import DataProvider
from app.shared.ohlcv.kraken_provider import KrakenProvider


class KrakenRepository(BaseRepository):
    """Repository for Kraken OHLCV data with caching.
    
    Wraps KrakenProvider and adds:
    - Time-based caching for repeated requests
    - Interface segregation via DataProvider Protocol
    """

    def __init__(self, provider: DataProvider | None = None) -> None:
        """Initialize repository with optional provider injection.
        
        Args:
            provider: DataProvider instance (creates default KrakenProvider if None)
        """
        super().__init__()
        self._provider = provider or KrakenProvider()
        self._cache: dict[tuple[str, int, int], tuple[list[dict[str, object]], float]] = {}
        self._cache_ttl = 300  # 5 minutes cache TTL

    async def fetch_ohlcv_data(
        self, pair: str, count: int, interval: int = 1
    ) -> list[dict[str, object]]:
        """Fetch OHLCV data with caching.
        
        Args:
            pair: Trading pair
            count: Number of candles
            interval: Time interval
            
        Returns:
            List of OHLCV dictionaries
        """
        cache_key = (pair, count, interval)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            self.logger.debug("Cache hit for %s", cache_key)
            return cached

        self.logger.debug("Cache miss for %s", cache_key)
        data = await self._provider.fetch_ohlcv_data(pair, count, interval)
        self._set_cache(cache_key, data)
        return data

    def _get_from_cache(self, key: tuple[str, int, int]) -> list[dict[str, object]] | None:
        """Get data from cache if valid."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def _set_cache(self, key: tuple[str, int, int], data: list[dict[str, object]]) -> None:
        """Store data in cache with current timestamp."""
        self._cache[key] = (data, time.time())

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self.logger.info("Repository cache cleared")
