"""
Tests for the HistoricDataService class.

Why mock httpx: Network calls in unit tests lead to flaky, slow test suites.
We inject a mocked Kraken JSON response using pytest-mock so the focus remains
entirely on validating data fetching and parsing operations.
"""

import pytest
from unittest.mock import Mock
from app.features.historic_data.service import HistoricDataService
from app.core.exceptions import DataFetchError


def test_fetch_hourly_ohlcv_success(mocker):
    """
    Simulates a successful Kraken API response. Validate that the service
    correctly parses the nested JSON, creates a DataFrame, and returns
    OHLCV data without reaching out to the live network.
    """
    service = HistoricDataService()
    pair = "XXBTZUSD"
    base_time = 1711000000
    dummy_data = []

    # Generate sample OHLCV data
    for i in range(168):  # 1 week of hourly data
        o = 60000.0 + (i % 10) * 10
        h = o + 500.0
        l = o - 500.0
        c = o + 100.0
        dummy_data.append(
            [
                base_time + i * 3600,  # timestamp
                str(o),
                str(h),
                str(l),
                str(c),  # open, high, low, close
                "60000.0",
                "1.5",
                10,  # vwap, volume, count
            ]
        )

    mock_payload = {
        "error": [],
        "result": {pair: dummy_data, "last": base_time + 167 * 3600},
    }

    mock_response = Mock()
    mock_response.json.return_value = mock_payload
    mock_response.raise_for_status.return_value = None

    # Override httpx.get globally during this test
    mocker.patch("httpx.get", return_value=mock_response)

    response = service.fetch_hourly_ohlcv(pair)

    # Assert basic response structure
    assert response.symbol == pair
    assert response.total_records == 168
    assert len(response.data) == 168

    # Verify OHLCV data structure on first and last records
    first_record = response.data[0]
    assert first_record.timestamp is not None
    assert first_record.open > 0
    assert first_record.high > 0
    assert first_record.low > 0
    assert first_record.close > 0
    assert first_record.volume >= 0

    last_record = response.data[-1]
    assert last_record.timestamp is not None
    assert last_record.open > 0
    assert last_record.high > 0
    assert last_record.low > 0
    assert last_record.close > 0
    assert last_record.volume >= 0


def test_fetch_hourly_ohlcv_api_error(mocker):
    """
    Simulates Kraken responding with an error inside the JSON payload.
    Ensure our system intercepts this and raises our domain `DataFetchError`.
    """
    service = HistoricDataService()
    pair = "INVALID"

    mock_payload = {"error": ["EQuery:Unknown asset pair"]}

    mock_response = Mock()
    mock_response.json.return_value = mock_payload
    mock_response.raise_for_status.return_value = None

    mocker.patch("httpx.get", return_value=mock_response)

    with pytest.raises(DataFetchError, match="Kraken API error"):
        service.fetch_hourly_ohlcv(pair)
