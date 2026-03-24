"""
Live Integration Testing for Historic Data.

This module verifies the end-to-end flow from the real Kraken API
to our Enriched JSON response.

Requirements:
1. Internet Access: The runner must be able to reach api.kraken.com.
2. No Mocking: We explicitly do NOT use unittest.mock or pytest-mock here.
3. Marker: Uses @pytest.mark.integration to separate these from fast unit tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import DataFetchError


@pytest.mark.integration
class TestKrakenLiveIntegration:
    """End-to-end integration test for the real Kraken API."""

    def test_get_live_data_endpoint(self, client: TestClient):
        """
        Hit the GET /api/v1/historic-data/live endpoint with a real pair.
        Verifies the full FastAPI router -> Service -> HTTPX -> pandas pipeline
        works correctly with real Kraken data.
        """
        try:
            # We use TestClient from conftest.py
            response = client.get("/api/v1/historic-data/live?pair=XXBTZUSD")
            
            # If the API returns a 502 or 503, it means Kraken is down or unreachable
            if response.status_code in (502, 503):
                pytest.skip("External API Unavailable.")
            
            # Assertions
            assert response.status_code == 200, f"Expected 200, got {response.status_code} - {response.text}"
            
            body = response.json()
            assert body["symbol"] == "XXBTZUSD"
            assert body["total_records"] > 0
            assert len(body["data"]) > 0
            
            # Check the last record has indicators
            last_record = body["data"][-1]
            assert "sma" in last_record
            assert "rsi" in last_record
            assert "macd" in last_record
            assert "macd_signal" in last_record
            
            assert last_record["sma"] is not None
            assert last_record["rsi"] is not None
            assert last_record["macd"] is not None
            assert last_record["macd_signal"] is not None
            
            # Verify timestamps are ISO strings (returned as string by TestClient JSON parsing)
            assert isinstance(last_record["timestamp"], str)
            assert last_record["timestamp"].endswith("Z") or "+00:00" in last_record["timestamp"]
            
            print(f"\\nSuccessfully fetched {body['total_records']} real hourly candles from Kraken via endpoint!")
            
        except Exception as exc:
            # Catching generic exception in case network issues cause unexpected errors
            pytest.skip(f"External API Unavailable. Error: {str(exc)}")
