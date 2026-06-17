"""Kraken OHLCV transport client with envelope validation.

This module isolates network access and upstream response-envelope checks so
downstream services can consume normalized payload dictionaries.
"""

import httpx
import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import DataFetchError

settings = get_settings()


class KrakenProvider:
    """HTTP client wrapper for Kraken OHLC endpoint interactions."""

    def __init__(
        self, base_url: str | None = None, timeout: float | None = None
    ) -> None:
        """Initialize Kraken API client with optional overrides."""
        self.base_url = base_url or settings.KRAKEN_OHLC_URL
        self.timeout = timeout or settings.KRAKEN_TIMEOUT

    async def fetch_ohlcv_data(
        self, pair: str, count: int, interval: int = 1
    ) -> list[dict[str, object]]:
        """Fetch raw OHLCV payload from Kraken and preprocess to standard format."""
        query_params = self._build_query_params(
            pair=pair, count=count, interval=interval
        )
        payload = await self._request_payload(pair=pair, query_params=query_params)
        self._validate_api_response(payload=payload, pair=pair)
        
        return self._preprocess_payload(payload=payload, pair=pair)
        
    def _preprocess_payload(self, payload: dict, pair: str) -> list[dict[str, object]]:
        """Map Kraken specific payload into standard OHLCV list of dicts."""
        try:
            result = payload["result"]
            pair_key = next(key for key in result if key != "last")
            raw_candles = result[pair_key]
            last_completed_candle = result["last"]

            # Exclude incomplete candle
            if raw_candles and last_completed_candle != raw_candles[-1][0]:
                raw_candles = raw_candles[:-1]

            return [
                {
                    "timestamp": c[0],
                    "open": c[1],
                    "high": c[2],
                    "low": c[3],
                    "close": c[4],
                    "volume": c[6],
                }
                for c in raw_candles
            ]
        except (KeyError, StopIteration, IndexError) as error:
            raise DataFetchError(f"Kraken processing error for '{pair}': {error}") from error

    def _build_query_params(
        self, pair: str, count: int, interval: int
    ) -> dict[str, int | str]:
        """Build Kraken OHLC query parameters for pair and time range."""
        # Note: We do NOT pass `count` to the Kraken OHLC endpoint because it ignores it.
        # Kraken returns the last 720 candles by default. We use `since` to filter.
        return {
            "pair": pair,
            "interval": interval,
            "since": self._calculate_since_timestamp(count, interval),
        }

    async def _request_payload(self, pair: str, query_params: dict[str, int | str]) -> dict:
        """Execute Kraken request and return parsed JSON payload."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params=query_params,
                    timeout=self.timeout,
                )
            response.raise_for_status()
        except httpx.RequestError as error:
            raise DataFetchError(
                f"Network error while fetching Kraken data for '{pair}': {error}"
            ) from error
        except httpx.HTTPStatusError as error:
            raise DataFetchError(
                f"HTTP error while fetching Kraken data for '{pair}': {error}"
            ) from error

        try:
            payload = response.json()
        except ValueError as error:
            raise DataFetchError(
                f"Invalid JSON response from Kraken for '{pair}': {error}"
            ) from error

        if not isinstance(payload, dict):
            raise DataFetchError(
                f"Invalid payload shape from Kraken for '{pair}': expected object"
            )

        return payload

    @staticmethod
    def _calculate_since_timestamp(count: int, interval: int) -> int:
        """Calculate Unix timestamp for 720 candles ago, UTC-aligned.
        
        Regardless of the `count` argument, we always request 720 candles 
        to ensure technical indicators have enough history.
        """
        now = pd.Timestamp.now(tz="UTC").floor("h")
        return int(now.timestamp() - (720 * interval * 60))

    @staticmethod
    def _validate_api_response(payload: dict, pair: str) -> None:
        """Validate Kraken API envelope fields and raise domain errors."""
        if payload.get("error"):
            raise DataFetchError(f"Kraken API error for '{pair}': {payload['error']}")
        if "result" not in payload:
            raise DataFetchError(f"Kraken response for '{pair}' missing 'result' field")
