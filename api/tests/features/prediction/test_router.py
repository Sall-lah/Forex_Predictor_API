from datetime import datetime, timezone
"""
Unit tests for prediction router endpoints.

Tests:
- POST /predict endpoint with mocked service
- Error handling (400, 422, 502, 503)
- Request validation
"""

from unittest.mock import Mock
import pytest

from app.core.config import Settings
from app.core.exceptions import (
    DataFetchError,
    InsufficientDataError,
    ModelNotLoadedError,
)
from app.main import app
from app.features.prediction.schemas import PredictionResponse


def test_prediction_response_success_with_probabilities() -> None:
    """Test PredictionResponse accepts canonical probability fields."""
    response = PredictionResponse(
        pair="XXBTZUSD",
        probability_up=0.72,
        probability_down=0.18,
        probability_straight=0.10,
        computed_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc)
    )

    assert response.probability_up == 0.72
    assert response.probability_down == 0.18
    assert response.probability_straight == 0.10


def test_prediction_response_success_serialization_contract_fields() -> None:
    """Test PredictionResponse serializes canonical response contract keys only."""
    payload = PredictionResponse(
        pair="XXBTZUSD",
        probability_up=0.72,
        probability_down=0.18,
        probability_straight=0.10,
        computed_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc)
    ).model_dump()

    assert {k: v for k, v in payload.items() if k not in ["computed_at", "valid_until"]} == {
        "pair": "XXBTZUSD",
        "probability_up": 0.72,
        "probability_down": 0.18,
        "probability_straight": 0.10,
    }


def test_predict_endpoint_success(client, mocker):
    """Test successful prediction via API endpoint."""
    # Mock the service's predict method
    mock_response = PredictionResponse(
        pair="XXBTZUSD",
        probability_up=0.72,
        probability_down=0.18,
        probability_straight=0.10,
        computed_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc)
    )

    # Patch the PredictionService class
    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value
    mock_service_instance.predict = mocker.AsyncMock(return_value=mock_response)

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {
            "pair",
            "probability_up",
            "probability_down",
            "probability_straight",
            "computed_at",
            "valid_until",
        }
    assert data["pair"] == "XXBTZUSD"
    assert data["probability_up"] == 0.72
    assert data["probability_down"] == 0.18
    assert data["probability_straight"] == 0.10


def test_predict_endpoint_ethusd(client, mocker):
    """Test prediction for ETHUSD asset."""
    # Mock the service
    mock_response = PredictionResponse(
        pair="XETHZUSD",
        probability_up=0.58,
        probability_down=0.32,
        probability_straight=0.10,
        computed_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc)
    )

    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value
    mock_service_instance.predict = mocker.AsyncMock(return_value=mock_response)

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XETHZUSD",
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {
            "pair",
            "probability_up",
            "probability_down",
            "probability_straight",
            "computed_at",
            "valid_until",
        }
    assert data["probability_up"] == 0.58
    assert data["probability_down"] == 0.32
    assert data["probability_straight"] == 0.10


def test_predict_endpoint_invalid_asset(client, mocker):
    """Test validation error for invalid asset name."""
    # Make request with invalid asset
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "",
        },
    )

    # Assert - Pydantic validation error (422)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_predict_endpoint_missing_fields(client):
    """Test validation error for missing required fields."""
    # Make request without pair
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            },
    )

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_predict_endpoint_empty_pair(client):
    """Test validation error for empty pair string."""
    # Make request with empty pair
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "",
        },
    )

    # Assert
    assert response.status_code == 422


def test_predict_endpoint_data_fetch_error(client, mocker):
    """Test handling of Kraken API fetch error (502)."""
    # Mock service to raise DataFetchError
    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value
    mock_service_instance.predict = mocker.AsyncMock(side_effect=DataFetchError("Kraken API unreachable"))

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
        },
    )

    # Assert - 502 Bad Gateway
    assert response.status_code == 502
    data = response.json()
    assert "Kraken API unreachable" in data["detail"]


def test_predict_endpoint_insufficient_data_error(client, mocker):
    """Test handling of insufficient data error (422)."""
    # Mock service to raise InsufficientDataError
    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value
    mock_service_instance.predict = mocker.AsyncMock(side_effect=InsufficientDataError("Need at least 168 rows"))

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
        },
    )

    # Assert - 422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()
    assert "168" in data["detail"]


def test_predict_endpoint_model_not_loaded_error(client, mocker):
    """Test handling of model loading error (503)."""
    # Mock service to raise ModelNotLoadedError
    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value
    mock_service_instance.predict = mocker.AsyncMock(side_effect=ModelNotLoadedError("Model file not found"))

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
        },
    )

    # Assert - 503 Service Unavailable
    assert response.status_code == 503
    data = response.json()
    assert "Model file not found" in data["detail"]


def test_predict_endpoint_probability_range(client, mocker):
    """Test that probability_up is within valid range [0.0, 1.0]."""
    app.dependency_overrides.clear()
    # Mock service with edge case probabilities
    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value

    # Test with 0.0
    mock_service_instance.predict = mocker.AsyncMock(return_value= PredictionResponse(
        pair="XXBTZUSD",
        probability_up=0.0,
        probability_down=1.0,
        probability_straight=0.0,
        computed_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc)
    ))

    response = client.post(
        "/api/v1/prediction/predict", json={"pair": "XXBTZUSD"}
    )

    assert response.status_code == 200
    assert response.json()["probability_up"] == 0.0
    assert response.json()["probability_down"] == 1.0
    assert response.json()["probability_straight"] == 0.0

    # Test with 1.0
    mock_service_instance.predict = mocker.AsyncMock(return_value= PredictionResponse(
        pair="XXBTZUSD",
        probability_up=1.0,
        probability_down=0.0,
        probability_straight=0.0,
        computed_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc)
    ))

    response = client.post(
        "/api/v1/prediction/predict", json={"pair": "XXBTZUSD"}
    )

    assert response.status_code == 200
    assert response.json()["probability_up"] == 1.0
    assert response.json()["probability_down"] == 0.0
    assert response.json()["probability_straight"] == 0.0
