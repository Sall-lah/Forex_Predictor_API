"""
Tests for the HistoricDataFeature router endpoints.

Tests verify FastAPI routing, schema serialization, and HTTP status codes
by mocking the service layer using dependency overrides.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.features.historic_data.router import get_service
from app.features.historic_data.schemas import HistoricDataResponse, OHLCVRecord

# Initialize FastAPI TestClient
client = TestClient(app)


class MockHistoricDataService:
    """Mock service returning predictable OHLCV data for testing."""

    def fetch_hourly_ohlcv(self, pair: str) -> HistoricDataResponse:
        """Return mock OHLCV data."""
        record = OHLCVRecord(
            timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=2.5,
        )
        return HistoricDataResponse(symbol=pair, total_records=1, data=[record])


def override_service():
    """Dependency override factory."""
    return MockHistoricDataService()


@pytest.fixture(autouse=True)
def override_dependency():
    """Apply mock service to FastAPI app for all tests."""
    app.dependency_overrides[get_service] = override_service
    yield
    app.dependency_overrides.clear()


def test_get_live_data_endpoint():
    """
    Verify /live endpoint returns correct OHLCV data.

    Tests that the endpoint successfully calls the service,
    serializes Pydantic models correctly, and returns 200 status.
    """
    pair = "XXBTZUSD"
    response = client.get(f"/api/v1/historic-data/live?pair={pair}")

    assert response.status_code == 200

    data = response.json()
    assert data["symbol"] == pair
    assert data["total_records"] == 1
    assert len(data["data"]) == 1

    # Verify OHLCV values from mocked service
    record = data["data"][0]
    assert record["open"] == 50000.0
    assert record["high"] == 51000.0
    assert record["low"] == 49000.0
    assert record["close"] == 50500.0
    assert record["volume"] == 2.5
    assert "timestamp" in record
