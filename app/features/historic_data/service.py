"""
Service layer for fetching and processing OHLCV data.

Architecture:
- KrakenAPIClient: Handles HTTP communication with Kraken API
- OHLCVDataFrame: Encapsulates DataFrame operations and validations
- HistoricDataService: Orchestrates the workflow and provides business logic
"""

import logging
from typing import List

import httpx
import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import (
    DataFetchError,
    DataValidationError,
    InsufficientDataError,
)
from app.features.historic_data.schemas import (
    HistoricDataRequest,
    HistoricDataResponse,
    OHLCVRecord,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class KrakenAPIClient:
    """
    Handles communication with Kraken public API.

    Responsibilities:
    - Make HTTP requests to Kraken
    - Parse API responses
    - Handle API errors
    """

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        """
        Initialize Kraken API client.

        Args:
            base_url: Kraken OHLC endpoint URL (defaults to config value)
            timeout: Request timeout in seconds (defaults to config value)
        """
        self.base_url = base_url or settings.KRAKEN_OHLC_URL
        self.timeout = timeout or settings.KRAKEN_TIMEOUT

    def fetch_ohlcv_data(self, pair: str, hours: int) -> dict:
        """
        Fetch raw OHLCV data from Kraken API.

        Args:
            pair: Trading pair (e.g., "XXBTZUSD")
            hours: Hours of historical data to fetch

        Returns:
            Raw JSON response from Kraken

        Raises:
            DataFetchError: If request fails or API returns error
        """
        since_timestamp = self._calculate_since_timestamp(hours)

        try:
            response = httpx.get(
                self.base_url,
                params={
                    "pair": pair,
                    "interval": settings.KRAKEN_HOURLY_INTERVAL,
                    "since": since_timestamp,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise DataFetchError(
                f"Failed to fetch data for '{pair}': {error}"
            ) from error

        self._validate_api_response(payload, pair)
        return payload

    @staticmethod
    def _calculate_since_timestamp(hours: int) -> int:
        """Calculate Unix timestamp for 'hours' ago."""
        now = pd.Timestamp.now(tz="UTC").floor("h")
        return int(now.timestamp() - (hours * 3600))

    @staticmethod
    def _validate_api_response(payload: dict, pair: str) -> None:
        """
        Validate Kraken API response for errors.

        Raises:
            DataFetchError: If API returned an error
        """
        if payload.get("error"):
            raise DataFetchError(f"Kraken API error for '{pair}': {payload['error']}")


class OHLCVDataFrame:
    """
    Encapsulates OHLCV data as a pandas DataFrame.

    Responsibilities:
    - Store and validate OHLCV data
    - Convert between different formats (Kraken JSON, DataFrame, Pydantic records)
    - Ensure data quality and completeness
    """

    REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize with a DataFrame.

        Args:
            dataframe: DataFrame with OHLCV columns
        """
        self.df = dataframe

    @classmethod
    def from_kraken_response(cls, payload: dict) -> "OHLCVDataFrame":
        """
        Create OHLCVDataFrame from Kraken API response.

        Args:
            payload: Raw JSON from Kraken API

        Returns:
            OHLCVDataFrame instance

        Raises:
            DataFetchError: If parsing fails
        """
        try:
            # Extract candle data from nested structure
            result = payload["result"]
            pair_key = next(k for k in result if k != "last")
            raw_candles = result[pair_key]

            # Create DataFrame with all Kraken columns
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

            # Convert data types
            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].astype(float)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

            # Keep only standard OHLCV columns
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]

            # Sort and reset index
            df = df.sort_values(by="timestamp").reset_index(drop=True)

            return cls(df)

        except (KeyError, ValueError, TypeError, StopIteration) as error:
            raise DataFetchError(f"Failed to parse Kraken response: {error}") from error

    @classmethod
    def from_records(cls, records: List[OHLCVRecord]) -> "OHLCVDataFrame":
        """
        Create OHLCVDataFrame from list of Pydantic records.

        Args:
            records: List of OHLCVRecord objects

        Returns:
            OHLCVDataFrame instance

        Raises:
            DataValidationError: If conversion fails
        """
        try:
            df = pd.DataFrame([record.dict() for record in records])
            return cls(df)
        except ValueError as error:
            raise DataValidationError(f"Invalid record structure: {error}") from error

    def to_records(self) -> List[OHLCVRecord]:
        """
        Convert DataFrame to list of Pydantic records.

        Returns:
            List of OHLCVRecord objects
        """
        # Replace NaN with None for JSON serialization
        clean_df = self.df.where(pd.notnull(self.df), None)
        return [OHLCVRecord(**row) for row in clean_df.to_dict(orient="records")]

    def validate_columns(self) -> None:
        """
        Validate that all required columns exist.

        Raises:
            DataValidationError: If columns are missing
        """
        missing = set(self.REQUIRED_COLUMNS) - set(self.df.columns)
        if missing:
            raise DataValidationError(f"Missing required columns: {', '.join(missing)}")

    def validate_row_count(self, min_rows: int) -> None:
        """
        Validate that DataFrame has enough rows.

        Args:
            min_rows: Minimum required rows

        Raises:
            InsufficientDataError: If row count is below minimum
        """
        row_count = len(self.df)
        if row_count < min_rows:
            raise InsufficientDataError(
                f"Only {row_count} rows found, but {min_rows} required"
            )

    def validate(self, min_rows: int = 1) -> None:
        """
        Run all validations.

        Args:
            min_rows: Minimum required rows
        """
        self.validate_columns()
        self.validate_row_count(min_rows)


class HistoricDataService:
    """
    Main service for fetching and processing historic OHLCV data.

    Responsibilities:
    - Coordinate data fetching from Kraken
    - Process and validate OHLCV data
    - Return data in standardized format
    """

    def __init__(self, api_client: KrakenAPIClient | None = None):
        """
        Initialize service with optional dependencies.

        Args:
            api_client: Client for Kraken API (defaults to KrakenAPIClient)
        """
        self.api_client = api_client or KrakenAPIClient()

    def fetch_hourly_ohlcv(self, pair: str) -> HistoricDataResponse:
        """
        Fetch 1 week of hourly OHLCV data from Kraken.

        Args:
            pair: Kraken trading pair (e.g., "XXBTZUSD")

        Returns:
            HistoricDataResponse with OHLCV records

        Raises:
            DataFetchError: If fetching or parsing fails
            InsufficientDataError: If insufficient data returned
            DataValidationError: If data validation fails
        """
        # Fetch raw data from Kraken
        payload = self.api_client.fetch_ohlcv_data(pair, settings.KRAKEN_DEFAULT_HOURS)

        # Parse and validate
        ohlcv_data = OHLCVDataFrame.from_kraken_response(payload)
        ohlcv_data.validate()

        # Convert to response format
        records = ohlcv_data.to_records()

        logger.info(
            "Fetched Kraken data for '%s' — %d hourly candles",
            pair,
            len(records),
        )

        return HistoricDataResponse(
            symbol=pair,
            total_records=len(records),
            data=records,
        )

    def compute_indicators(self, request: HistoricDataRequest) -> HistoricDataResponse:
        """
        Process provided OHLCV data and return it.

        Args:
            request: Request containing OHLCV records

        Returns:
            HistoricDataResponse with validated OHLCV records

        Raises:
            InsufficientDataError: If insufficient data provided
            DataValidationError: If data has structural issues
        """
        # Convert and validate
        ohlcv_data = OHLCVDataFrame.from_records(request.records)
        ohlcv_data.validate()

        # Convert back to response format
        records = ohlcv_data.to_records()

        logger.info(
            "Processed OHLCV data for %s — %d records",
            request.symbol,
            len(records),
        )

        return HistoricDataResponse(
            symbol=request.symbol,
            total_records=len(records),
            data=records,
        )
