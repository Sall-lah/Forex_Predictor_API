"""Regression tests for shared Kraken OHLCV primitives."""

from unittest.mock import Mock

import httpx
import pandas as pd
import pytest

from app.core.exceptions import (
    DataFetchError,
    DataValidationError,
    InsufficientDataError,
)
from app.core.ohlcv import KrakenAPIClient, OHLCVDataFrame


def test_fetch_ohlcv_data_maps_transport_failures_to_data_fetch_error(mocker) -> None:
    """Transport failures should map to a stable DataFetchError contract."""
    client = KrakenAPIClient(base_url="https://api.kraken.test")
    mocker.patch("httpx.get", side_effect=httpx.ConnectTimeout("timeout"))

    with pytest.raises(
        DataFetchError, match="Network error while fetching Kraken data"
    ):
        client.fetch_ohlcv_data(pair="XXBTZUSD", hours=24)


def test_from_kraken_response_parses_payload_and_drops_incomplete_latest_candle() -> (
    None
):
    """Parser should normalize OHLCV columns and drop incomplete tail row."""
    base_time = 1711000000
    payload = {
        "error": [],
        "result": {
            "XXBTZUSD": [
                [
                    base_time,
                    "50000.0",
                    "51000.0",
                    "49000.0",
                    "50500.0",
                    "50200.0",
                    "100.5",
                    150,
                ],
                [
                    base_time + 3600,
                    "50500.0",
                    "51500.0",
                    "49500.0",
                    "51000.0",
                    "50700.0",
                    "120.5",
                    180,
                ],
            ],
            "last": base_time,
        },
    }

    parsed = OHLCVDataFrame.from_kraken_response(payload)

    assert list(parsed.df.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert len(parsed.df) == 1
    assert pd.api.types.is_datetime64tz_dtype(parsed.df["timestamp"])


def test_validate_raises_for_missing_columns_and_insufficient_rows() -> None:
    """Validation should map structural issues to domain exceptions."""
    missing_columns_df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2024-01-01", tz="UTC")],
            "open": [1.0],
            "high": [2.0],
            "low": [0.5],
            "close": [1.5],
        }
    )

    with pytest.raises(DataValidationError, match="Missing required columns"):
        OHLCVDataFrame(missing_columns_df).validate()

    too_few_rows_df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2024-01-01", tz="UTC")],
            "open": [1.0],
            "high": [2.0],
            "low": [0.5],
            "close": [1.5],
            "volume": [10.0],
        }
    )

    with pytest.raises(InsufficientDataError, match="2 required"):
        OHLCVDataFrame(too_few_rows_df).validate(min_rows=2)
