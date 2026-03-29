"""
Unit tests for prediction router endpoints.

Tests:
- POST /predict endpoint with mocked service
- Error handling (400, 422, 502, 503)
- Request validation
"""

from unittest.mock import Mock
import pytest

from app.core.exceptions import (
    DataFetchError,
    InsufficientDataError,
    ModelNotLoadedError,
)
from app.features.prediction.schemas import PredictionResponse


def test_predict_endpoint_success(client, mocker):
    """Test successful prediction via API endpoint."""
    # Mock the service's predict method
    mock_response = PredictionResponse(
        pair="XXBTZUSD",
        asset="BTCUSD",
        probability_up=0.72,
    )

    # Patch the PredictionService class
    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value
    mock_service_instance.predict.return_value = mock_response

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
            "asset": "BTCUSD",
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["pair"] == "XXBTZUSD"
    assert data["asset"] == "BTCUSD"
    assert data["probability_up"] == 0.72


def test_predict_endpoint_ethusd(client, mocker):
    """Test prediction for ETHUSD asset."""
    # Mock the service
    mock_response = PredictionResponse(
        pair="XETHZUSD",
        asset="ETHUSD",
        probability_up=0.58,
    )

    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value
    mock_service_instance.predict.return_value = mock_response

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XETHZUSD",
            "asset": "ETHUSD",
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["asset"] == "ETHUSD"
    assert data["probability_up"] == 0.58


def test_predict_endpoint_invalid_asset(client):
    """Test validation error for invalid asset name."""
    # Make request with invalid asset
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
            "asset": "INVALID",
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
            "asset": "BTCUSD",
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
            "asset": "BTCUSD",
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
    mock_service_instance.predict.side_effect = DataFetchError("Kraken API unreachable")

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
            "asset": "BTCUSD",
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
    mock_service_instance.predict.side_effect = InsufficientDataError(
        "Need at least 168 rows"
    )

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
            "asset": "BTCUSD",
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
    mock_service_instance.predict.side_effect = ModelNotLoadedError(
        "Model file not found"
    )

    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "XXBTZUSD",
            "asset": "BTCUSD",
        },
    )

    # Assert - 503 Service Unavailable
    assert response.status_code == 503
    data = response.json()
    assert "Model file not found" in data["detail"]


def test_predict_endpoint_probability_range(client, mocker):
    """Test that probability_up is within valid range [0.0, 1.0]."""
    # Mock service with edge case probabilities
    mock_service_class = mocker.patch(
        "app.features.prediction.router.PredictionService"
    )
    mock_service_instance = mock_service_class.return_value

    # Test with 0.0
    mock_service_instance.predict.return_value = PredictionResponse(
        pair="XXBTZUSD",
        asset="BTCUSD",
        probability_up=0.0,
    )

    response = client.post(
        "/api/v1/prediction/predict", json={"pair": "XXBTZUSD", "asset": "BTCUSD"}
    )

    assert response.status_code == 200
    assert response.json()["probability_up"] == 0.0

    # Test with 1.0
    mock_service_instance.predict.return_value = PredictionResponse(
        pair="XXBTZUSD",
        asset="BTCUSD",
        probability_up=1.0,
    )

    response = client.post(
        "/api/v1/prediction/predict", json={"pair": "XXBTZUSD", "asset": "BTCUSD"}
    )

    assert response.status_code == 200
    assert response.json()["probability_up"] == 1.0
