"""
Service layer for computing technical indicators on OHLCV data.

Why OOP: Encapsulating indicator logic in a class allows us to
inject configuration, swap implementations for testing, and
extend with caching or async fetching later without touching
the router.
"""

import logging
from typing import List

import httpx
import pandas as pd
import ta

from app.core.exceptions import DataFetchError, DataValidationError, InsufficientDataError
from app.features.historic_data.schemas import (
    EnrichedOHLCVRecord,
    HistoricDataRequest,
    HistoricDataResponse,
    OHLCVRecord,
)

logger = logging.getLogger(__name__)

# Kraken public REST endpoint for OHLC data.
_KRAKEN_OHLC_URL = "https://api.kraken.com/0/public/OHLC"
# Hourly interval in minutes as required by Kraken.
_KRAKEN_HOURLY_INTERVAL = 60
# Default SMA / RSI windows used when fetching live Kraken data.
_DEFAULT_SMA_PERIOD = 14
_DEFAULT_RSI_PERIOD = 14


class HistoricDataService:
    """
    Processes raw OHLCV records and enriches them with technical indicators.

    All heavy lifting uses vectorised pandas / ta-lib operations —
    no iterrows() is used anywhere.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Kraken live-data fetching
    # ------------------------------------------------------------------

    def fetch_hourly_ohlcv(self, pair: str) -> HistoricDataResponse:
        """
        Fetch the last 30 days of hourly OHLCV data from Kraken, enrich
        with SMA, RSI, MACD indicators, and return a HistoricDataResponse.

        Why httpx: It supports both sync and async and is already in our
        requirements.  We use the synchronous client here so the method
        signature stays simple for FastAPI's sync dependency injection.

        Args:
            pair: Kraken asset-pair identifier, e.g. ``"XXBTZUSD"``.

        Returns:
            HistoricDataResponse with enriched OHLCV records.

        Raises:
            DataFetchError: On any network failure, non-2xx HTTP status,
                            or error returned inside the Kraken JSON body.
        """
        try:
            response = httpx.get(
                _KRAKEN_OHLC_URL,
                params={"pair": pair, "interval": _KRAKEN_HOURLY_INTERVAL},
                timeout=15.0,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise DataFetchError(
                f"Network error while fetching Kraken data for '{pair}': {exc}"
            ) from exc

        if payload.get("error"):
            raise DataFetchError(
                f"Kraken API returned an error for '{pair}': {payload['error']}"
            )

        try:
            df = self._parse_kraken_response(payload)
        except (KeyError, ValueError, TypeError, StopIteration) as exc:
            raise DataFetchError(
                f"Failed to parse Kraken response for '{pair}': {exc}"
            ) from exc

        # MACD needs at least 26 rows; use max of all windows as guard.
        max_period = max(_DEFAULT_SMA_PERIOD, _DEFAULT_RSI_PERIOD, 26)
        self._validate_dataframe(df, max_period)

        df = self._enrich_dataframe(df, _DEFAULT_SMA_PERIOD, _DEFAULT_RSI_PERIOD)
        enriched_records = self._dataframe_to_records(df)

        logger.info(
            "Fetched and enriched Kraken data for '%s' — %d hourly candles.",
            pair,
            len(enriched_records),
        )

        return HistoricDataResponse(
            symbol=pair,
            total_records=len(enriched_records),
            data=enriched_records,
        )

    def compute_indicators(self, request: HistoricDataRequest) -> HistoricDataResponse:
        """
        Accept validated OHLCV data, compute indicators (SMA, RSI, MACD, MACD_signal),
        and return an enriched response.

        Args:
            request: Validated HistoricDataRequest containing raw candles
                     and desired indicator periods.

        Returns:
            HistoricDataResponse with original OHLCV data plus indicator
            columns.

        Raises:
            InsufficientDataError: When the number of candles is less than
                                   the requested indicator window.
            DataValidationError:   When the data contains structural issues
                                   that prevent computation.
        """
        df = self._records_to_dataframe(request.records)
        # MACD default slowest window is 26
        max_period = max(request.sma_period, request.rsi_period, 26)
        self._validate_dataframe(df, max_period)

        df = self._enrich_dataframe(df, request.sma_period, request.rsi_period)
        enriched_records = self._dataframe_to_records(df)

        logger.info(
            "Computed indicators for %s — %d records, SMA(%d), RSI(%d), MACD(12,26,9)",
            request.symbol,
            len(enriched_records),
            request.sma_period,
            request.rsi_period,
        )

        return HistoricDataResponse(
            symbol=request.symbol,
            total_records=len(enriched_records),
            data=enriched_records,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_kraken_response(payload: dict) -> pd.DataFrame:
        """
        Convert raw Kraken OHLC JSON payload to a typed DataFrame.

        Kraken embeds the candle arrays under a dynamic key matching the
        pair name (e.g. ``XXBTZUSD``).  We skip the ``'last'`` sentinel
        key that Kraken appends for pagination.

        Each raw candle is:
        ``[time, open, high, low, close, vwap, volume, count]``
        """
        # Find the data key — it is the only non-'last' key in result.
        result = payload["result"]
        pair_key = next(k for k in result if k != "last")
        raw_candles = result[pair_key]

        df = pd.DataFrame(
            raw_candles,
            columns=["timestamp", "open", "high", "low", "close", "vwap", "volume", "count"],
        )

        # Cast price/volume columns from Kraken's string representation.
        numeric_cols = ["open", "high", "low", "close", "volume"]
        df[numeric_cols] = df[numeric_cols].astype(float)

        # Unix → UTC datetime.
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

        # Drop Kraken-specific columns irrelevant to our pipeline.
        df = df.drop(columns=["vwap", "count"])
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def _enrich_dataframe(df: pd.DataFrame, sma_period: int, rsi_period: int) -> pd.DataFrame:
        """
        Apply all TA indicators to *df* in one place.

        Why a compositor: Both ``fetch_hourly_ohlcv`` and
        ``compute_indicators`` need the same three enrichment steps.
        Centralising them here prevents duplication and makes the
        indicator list easy to extend.
        """
        df = HistoricDataService._add_sma(df, sma_period)
        df = HistoricDataService._add_rsi(df, rsi_period)
        df = HistoricDataService._add_macd(df)
        return df

    @staticmethod
    def _records_to_dataframe(records: List[OHLCVRecord]) -> pd.DataFrame:
        """
        Convert a list of Pydantic OHLCVRecord models into a DataFrame.

        Why model_dump(): It is the Pydantic v2 method for serialising
        models to dicts, which pd.DataFrame() can consume directly
        without row-by-row iteration.
        """
        data = [record.model_dump() for record in records]
        df = pd.DataFrame(data)
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def _validate_dataframe(df: pd.DataFrame, min_rows: int) -> None:
        """
        Guard against edge-cases before running indicator calculations.

        Raises:
            DataValidationError:   If required OHLCV columns are missing.
            InsufficientDataError: If the row count is below the largest
                                   requested indicator window.
        """
        required_columns = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required_columns - set(df.columns)
        if missing:
            raise DataValidationError(
                f"Missing required columns: {', '.join(sorted(missing))}"
            )

        if len(df) < min_rows:
            raise InsufficientDataError(
                f"Need at least {min_rows} records for the requested "
                f"indicator windows, but only {len(df)} were provided."
            )

    @staticmethod
    def _add_sma(df: pd.DataFrame, period: int) -> pd.DataFrame:
        """
        Add a Simple Moving Average column to the DataFrame.

        Uses the `ta` library's SMAIndicator for consistency with
        the rest of the technical-analysis pipeline.
        """
        sma_indicator = ta.trend.SMAIndicator(close=df["close"], window=period)
        df["sma"] = sma_indicator.sma_indicator()
        return df

    @staticmethod
    def _add_rsi(df: pd.DataFrame, period: int) -> pd.DataFrame:
        """
        Add a Relative Strength Index column to the DataFrame.

        RSI is calculated using the `ta` library which implements the
        standard Wilder smoothing method internally.
        """
        rsi_indicator = ta.momentum.RSIIndicator(close=df["close"], window=period)
        df["rsi"] = rsi_indicator.rsi()
        return df

    @staticmethod
    def _add_macd(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add MACD and MACD Signal columns to the DataFrame.

        Uses the `ta` library's MACD indicator with standard 12/26/9 settings.
        """
        macd_indicator = ta.trend.MACD(
            close=df["close"],
            window_slow=26,
            window_fast=12,
            window_sign=9
        )
        df["macd"] = macd_indicator.macd()
        df["macd_signal"] = macd_indicator.macd_signal()
        return df

    @staticmethod
    def _dataframe_to_records(df: pd.DataFrame) -> List[EnrichedOHLCVRecord]:
        """
        Convert an enriched DataFrame back to a list of Pydantic models.

        Why .where(pd.notnull(...)): Replaces NaN with None so that
        Pydantic serialises them as JSON null rather than the string
        'NaN', which is invalid JSON.
        """
        df = df.where(pd.notnull(df), None)
        return [
            EnrichedOHLCVRecord(**row)
            for row in df.to_dict(orient="records")
        ]
