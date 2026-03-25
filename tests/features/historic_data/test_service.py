"""
Tests for the HistoricDataService class.

Why mock httpx: Network calls in unit tests lead to flaky, slow test suites. 
We inject a mocked Kraken JSON response using pytest-mock so the focus remains 
entirely on validating Pandas processing and TA indicator operations.
"""

import pytest
from unittest.mock import Mock
from app.features.historic_data.service import HistoricDataService
from app.core.exceptions import DataFetchError


def test_fetch_hourly_ohlcv_success(mocker):
    """
    Simulates a successful Kraken API response. Validate that the service 
    correctly parses the nested JSON, creates a DataFrame, and processes 
    indicators without reaching out to the live network.
    """
    service = HistoricDataService()
    pair = "XXBTZUSD"
    base_time = 1711000000
    dummy_data = []
    
    # Generate 30 rows to satisfy the MACD lookback requirement (minimum 26 rows)
    for i in range(30):
        dummy_data.append([
            base_time + i * 3600,                           # timestamp
            "60000.0", "61000.0", "59000.0",                 # open, high, low
            str(60000.0 + i * 10), "60000.0", "1.5", 10      # close, vwap, volume, count
        ])
    
    mock_payload = {
        "error": [],
        "result": {
            pair: dummy_data,
            "last": base_time + 29 * 3600
        }
    }
    
    mock_response = Mock()
    mock_response.json.return_value = mock_payload
    mock_response.raise_for_status.return_value = None
    
    # Override httpx.get globally during this test
    mocker.patch("httpx.get", return_value=mock_response)
    
    response = service.fetch_hourly_ohlcv(pair)
    
    # Assert
    assert response.symbol == pair
    assert response.total_records == 30
    assert len(response.data) == 30
    
    # Verify that indicators are correctly computed on the final record
    last_record = response.data[-1]
    assert last_record.sma is not None
    assert isinstance(last_record.sma, float)
    assert last_record.rsi is not None
    assert isinstance(last_record.rsi, float)
    assert last_record.macd is not None
    assert isinstance(last_record.macd, float)
    assert last_record.macd_signal is not None
    assert isinstance(last_record.macd_signal, float)


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
    
    with pytest.raises(DataFetchError, match="Kraken API returned an error"):
        service.fetch_hourly_ohlcv(pair)
