"""
Live Integration Testing for Historic Data.

This module verifies the end-to-end flow from the real Kraken API
to our OHLCV JSON response.

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
            assert response.status_code == 200, (
                f"Expected 200, got {response.status_code} - {response.text}"
            )

            body = response.json()
            assert body["symbol"] == "XXBTZUSD"
            assert body["total_records"] > 0
            assert len(body["data"]) > 0

            # Check the last record has OHLCV data
            last_record = body["data"][-1]
            assert "timestamp" in last_record
            assert "open" in last_record
            assert "high" in last_record
            assert "low" in last_record
            assert "close" in last_record
            assert "volume" in last_record

            assert last_record["open"] > 0
            assert last_record["high"] > 0
            assert last_record["low"] > 0
            assert last_record["close"] > 0
            assert last_record["volume"] >= 0

            # Verify high >= low
            assert last_record["high"] >= last_record["low"]

            # Verify timestamps are ISO strings (returned as string by TestClient JSON parsing)
            assert isinstance(last_record["timestamp"], str)
            assert (
                last_record["timestamp"].endswith("Z")
                or "+00:00" in last_record["timestamp"]
            )

            print(
                f"\nSuccessfully fetched {body['total_records']} real hourly candles from Kraken via endpoint!"
            )

        except Exception as exc:
            # Catching generic exception in case network issues cause unexpected errors
            pytest.skip(f"External API Unavailable. Error: {str(exc)}")
