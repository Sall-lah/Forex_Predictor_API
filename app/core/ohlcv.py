"""Shared Kraken OHLCV primitives reused across feature services.

This module centralizes transport, payload parsing, and DataFrame validation logic
so feature services can focus on orchestration only.
"""

import httpx
import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import (
    DataFetchError,
    DataValidationError,
    InsufficientDataError,
)

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


class OHLCVDataFrame:
    """Encapsulates OHLCV parsing, validation, and record conversion."""

    REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

    def __init__(self, dataframe: pd.DataFrame) -> None:
        """Initialize wrapper with an OHLCV DataFrame."""
        self.df = dataframe

    @classmethod
    def from_kraken_response(cls, payload: dict) -> "OHLCVDataFrame":
        """Parse Kraken payload into normalized OHLCV DataFrame."""
        try:
            result = payload["result"]
            pair_key = next(key for key in result if key != "last")
            raw_candles = result[pair_key]
            last_completed_candle = result["last"]

            df = pd.DataFrame(
                raw_candles,
                columns=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "vwap",
                    "volume",
                    "count",
                ],
            )

            if not df.empty and last_completed_candle != df.iloc[-1]["timestamp"]:
                df = df.iloc[:-1]

            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].astype(float)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            df = df.set_index("timestamp").sort_index().reset_index(drop=False)

            return cls(df)

        except (KeyError, ValueError, TypeError, StopIteration) as error:
            raise DataFetchError(f"Failed to parse Kraken response: {error}") from error

    def to_records(self) -> list[dict[str, object]]:
        """Convert DataFrame rows into JSON-safe dictionaries."""
        clean_df = self.df.where(pd.notnull(self.df), None)
        return clean_df.to_dict(orient="records")

    def validate_columns(self) -> None:
        """Validate that all required OHLCV columns are present."""
        missing = sorted(set(self.REQUIRED_COLUMNS) - set(self.df.columns))
        if missing:
            raise DataValidationError(f"Missing required columns: {', '.join(missing)}")

    def validate_row_count(self, min_rows: int) -> None:
        """Validate minimum DataFrame row count."""
        row_count = len(self.df)
        if row_count < min_rows:
            raise InsufficientDataError(
                f"Only {row_count} rows found, but {min_rows} required"
            )

    def validate(self, min_rows: int = 1) -> None:
        """Run required-column and minimum-row validations."""
        self.validate_columns()
        self.validate_row_count(min_rows)
