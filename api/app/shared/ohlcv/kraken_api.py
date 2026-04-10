"""Kraken OHLCV transport client with envelope validation.

This module isolates network access and upstream response-envelope checks so
downstream services can consume normalized payload dictionaries.
"""

import httpx
import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import DataFetchError

settings = get_settings()


class KrakenAPIClient:
    """HTTP client wrapper for Kraken OHLC endpoint interactions."""

    def __init__(
        self, base_url: str | None = None, timeout: float | None = None
    ) -> None:
        """Initialize Kraken API client with optional overrides."""
        self.base_url = base_url or settings.KRAKEN_OHLC_URL
        self.timeout = timeout or settings.KRAKEN_TIMEOUT

    def fetch_ohlcv_data(self, pair: str, hours: int) -> dict:
        """Fetch raw OHLCV payload from Kraken for a pair/time window."""
        query_params = self._build_query_params(pair=pair, hours=hours)
        payload = self._request_payload(pair=pair, query_params=query_params)
        self._validate_api_response(payload=payload, pair=pair)
        return payload

    def _build_query_params(self, pair: str, hours: int) -> dict[str, int | str]:
        """Build Kraken OHLC query parameters for pair and time range."""
        return {
            "pair": pair,
            "interval": settings.KRAKEN_HOURLY_INTERVAL,
            "since": self._calculate_since_timestamp(hours),
        }

    def _request_payload(self, pair: str, query_params: dict[str, int | str]) -> dict:
        """Execute Kraken request and return parsed JSON payload."""
        try:
            response = httpx.get(
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
    def _calculate_since_timestamp(hours: int) -> int:
        """Calculate Unix timestamp for hours ago, UTC-aligned."""
        now = pd.Timestamp.now(tz="UTC").floor("h")
        return int(now.timestamp() - (hours * 3600))

    @staticmethod
    def _validate_api_response(payload: dict, pair: str) -> None:
        """Validate Kraken API envelope fields and raise domain errors."""
        if payload.get("error"):
            raise DataFetchError(f"Kraken API error for '{pair}': {payload['error']}")
        if "result" not in payload:
            raise DataFetchError(f"Kraken response for '{pair}' missing 'result' field")
