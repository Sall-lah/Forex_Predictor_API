"""Regression tests for shared Kraken OHLCV primitives."""

from unittest.mock import Mock

import httpx
import pandas as pd
import pytest

pytestmark = pytest.mark.asyncio

from app.core.exceptions import (
    DataFetchError,
    DataValidationError,
    InsufficientDataError,
)
from app.shared.ohlcv import KrakenProvider, OHLCVDataFrame


async def test_fetch_ohlcv_data_maps_transport_failures_to_data_fetch_error(mocker) -> None:
    """Transport failures should map to a stable DataFetchError contract."""
    client = KrakenProvider(base_url="https://api.kraken.test")
    
    mock_client = mocker.AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.side_effect = httpx.ConnectTimeout("timeout")
    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    with pytest.raises(
        DataFetchError, match="Network error while fetching Kraken data"
    ):
        await client.fetch_ohlcv_data(pair="XXBTZUSD", count=24, interval=60)

async def test_fetch_ohlcv_data_query_params(mocker) -> None:
    """Ensure count is not in query params and since covers 720 candles."""
    client = KrakenProvider(base_url="https://api.kraken.test")
    
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"error": [], "result": {"XXBTZUSD": [], "last": 0}}
    
    mock_client = mocker.AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    await client.fetch_ohlcv_data(pair="XXBTZUSD", count=24, interval=60)
    
    call_kwargs = mock_client.get.call_args.kwargs
    params = call_kwargs["params"]
    
    assert "count" not in params
    assert params["interval"] == 60
    
    now = pd.Timestamp.now(tz="UTC").floor("h")
    expected_since = int(now.timestamp() - (720 * 60 * 60))
    assert params["since"] == expected_since


def test_from_provider_response_parses_payload_and_keeps_all_candles() -> (
    None
):
    """Provider should normalize OHLCV columns and keep all candles including incomplete."""
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

    client = KrakenProvider(base_url="https://api.kraken.test")
    preprocessed = client._preprocess_payload(payload, "XXBTZUSD")
    parsed = OHLCVDataFrame.from_provider_response(preprocessed)

    assert list(parsed.df.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    # Both candles are kept, including the incomplete one
    assert len(parsed.df) == 2
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
