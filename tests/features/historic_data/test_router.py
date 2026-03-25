"""
Tests for the HistoricDataFeature router endpoints.

Why use dependency overrides: Decoupling the HTTP router from the
heavy Pandas/TA underlying service logic allows us to verify FastAPI routing,
schema serialization, and HTTP status codes cleanly and quickly.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.features.historic_data.router import get_historic_data_service
from app.features.historic_data.schemas import HistoricDataResponse, EnrichedOHLCVRecord

# Initialize FastAPI TestClient
client = TestClient(app)


class MockHistoricDataService:
    """Mock implementation returning predictable data for router assertion."""
    
    def fetch_hourly_ohlcv(self, pair: str) -> HistoricDataResponse:
        record = EnrichedOHLCVRecord(
            timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=2.5,
            sma=50200.0,
            rsi=55.5,
            macd=120.5,
            macd_signal=100.0
        )
        return HistoricDataResponse(
            symbol=pair,
            total_records=1,
            data=[record]
        )


def override_get_historic_data_service():
    """Dependency override factory."""
    return MockHistoricDataService()


@pytest.fixture(autouse=True)
def override_dependency():
    """Automatically applies the mock to the FastAPI app for all tests in this file."""
    app.dependency_overrides[get_historic_data_service] = override_get_historic_data_service
    yield
    app.dependency_overrides.clear()


def test_get_live_data_endpoint():
    """
    Verifies that the /live endpoint successfully calls our injected Service Class, 
    packs the Pydantic models correctly, and returns a 200 JSON payload.
    """
    pair = "XXBTZUSD"
    # Ensure this matches the prefix routing registered in your app.api.router
    response = client.get(f"/api/v1/historic-data/live?pair={pair}")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["symbol"] == pair
    assert data["total_records"] == 1
    assert len(data["data"]) == 1
    
    # Assert values from the mocked service
    record = data["data"][0]
    assert record["open"] == 50000.0
    assert record["close"] == 50500.0
    assert record["sma"] == 50200.0
    assert record["rsi"] == 55.5
    assert record["macd"] == 120.5
    assert record["macd_signal"] == 100.0
    assert "timestamp" in record
