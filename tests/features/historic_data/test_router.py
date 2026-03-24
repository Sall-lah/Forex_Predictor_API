"""
HTTP-level tests for the Historic Data router.

Strategy:
- Use FastAPI's ``app.dependency_overrides`` to inject a ``MockService``
  that returns hard-coded data.  This completely decouples the router
  tests from the Kraken network and all pandas/ta computation.
- The TestClient from ``conftest.py`` drives real ASGI request/response
  cycles, exercising routing, serialisation, and status codes.
"""

from datetime import datetime, timezone
from typing import List
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.features.historic_data.router import get_historic_data_service
from app.features.historic_data.schemas import (
    EnrichedOHLCVRecord,
    HistoricDataResponse,
)
from app.core.exceptions import DataFetchError


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

_TS = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

_ENRICHED_RECORD = EnrichedOHLCVRecord(
    timestamp=_TS,
    open=84000.0,
    high=84100.0,
    low=83900.0,
    close=84050.0,
    volume=10.5,
    sma=84000.0,
    rsi=55.0,
    macd=12.5,
    macd_signal=11.0,
)

_MOCK_RESPONSE = HistoricDataResponse(
    symbol="XXBTZUSD",
    total_records=1,
    data=[_ENRICHED_RECORD],
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_service() -> MagicMock:
    """
    Create a MagicMock whose ``fetch_hourly_ohlcv`` and
    ``compute_indicators`` return pre-built responses.

    Why MagicMock: We only need to verify the HTTP layer; all service
    logic is covered by test_service.py.  A mock isolates the router
    completely from pandas/ta/httpx dependencies.
    """
    svc = MagicMock()
    svc.fetch_hourly_ohlcv.return_value = _MOCK_RESPONSE
    svc.compute_indicators.return_value = _MOCK_RESPONSE
    return svc


@pytest.fixture
def client(mock_service: MagicMock) -> TestClient:
    """
    Override the DI factory so the router always receives ``mock_service``.

    Why dependency_overrides: FastAPI provides this hook precisely for
    test isolation; it does not require modifying application code.
    """
    app.dependency_overrides[get_historic_data_service] = lambda: mock_service
    yield TestClient(app)
    # Restore originals so this fixture does not leak into other tests.
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/v1/historic-data/live
# ---------------------------------------------------------------------------

class TestGetLiveData:
    """Tests for the Kraken live-data endpoint."""

    def test_returns_200_and_valid_schema(self, client: TestClient):
        """Happy path: valid pair returns 200 with HistoricDataResponse shape."""
        response = client.get("/api/v1/historic-data/live", params={"pair": "XXBTZUSD"})

        assert response.status_code == 200
        body = response.json()
        assert body["symbol"] == "XXBTZUSD"
        assert body["total_records"] == 1
        assert len(body["data"]) == 1

        record = body["data"][0]
        for field in ("open", "high", "low", "close", "volume", "sma", "rsi", "macd", "macd_signal"):
            assert field in record, f"Field '{field}' missing from response record"

    def test_service_called_with_correct_pair(self, client: TestClient, mock_service: MagicMock):
        """Router must forward the ``pair`` query param to the service untouched."""
        client.get("/api/v1/historic-data/live", params={"pair": "ETHUSD"})
        mock_service.fetch_hourly_ohlcv.assert_called_once_with("ETHUSD")

    def test_missing_pair_returns_422(self, client: TestClient):
        """Omitting the required ``pair`` param must yield HTTP 422."""
        response = client.get("/api/v1/historic-data/live")
        assert response.status_code == 422

    def test_data_fetch_error_returns_502(self, client: TestClient, mock_service: MagicMock):
        """
        When the service raises DataFetchError (upstream failure), the
        global handler must translate it to HTTP 502 Bad Gateway.
        """
        mock_service.fetch_hourly_ohlcv.side_effect = DataFetchError("Kraken unreachable")
        response = client.get("/api/v1/historic-data/live", params={"pair": "XXBTZUSD"})
        assert response.status_code == 502
        assert "Kraken unreachable" in response.json()["detail"]


# ---------------------------------------------------------------------------
# POST /api/v1/historic-data/compute-indicators  (regression)
# ---------------------------------------------------------------------------

class TestComputeIndicatorsEndpoint:
    """Regression tests for the existing POST endpoint."""

    def _minimal_payload(self, n: int = 1) -> dict:
        return {
            "symbol": "BTC/USD",
            "records": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "open": 84000.0,
                    "high": 84100.0,
                    "low": 83900.0,
                    "close": 84050.0,
                    "volume": 10.5,
                }
            ] * n,
        }

    def test_returns_200_on_valid_payload(self, client: TestClient):
        response = client.post(
            "/api/v1/historic-data/compute-indicators",
            json=self._minimal_payload(),
        )
        assert response.status_code == 200
        assert response.json()["symbol"] == "XXBTZUSD"  # mock returns XXBTZUSD

    def test_missing_records_returns_422(self, client: TestClient):
        response = client.post(
            "/api/v1/historic-data/compute-indicators",
            json={"symbol": "BTC/USD"},
        )
        assert response.status_code == 422
