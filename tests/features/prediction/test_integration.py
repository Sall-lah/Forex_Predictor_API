"""
Live integration tests for prediction feature.

These tests make real API calls to Kraken and use the actual ML model.
They should be run sparingly to avoid rate limiting.

Run with: pytest tests/features/prediction/test_integration.py -v
"""

import pytest

from app.core.config import get_settings
from app.core.exceptions import DataFetchError
from app.features.prediction.service import PredictionService
from app.features.prediction.schemas import PredictionRequest


@pytest.mark.integration
def test_predict_btcusd_live():
    """
    Live test: Fetch real data from Kraken and make prediction for BTC/USD.

    Requirements:
    - Internet connection
    - Kraken API accessible
    - ML model file exists at app/features/prediction/ml_models/lightgbm_model_forex.pkl

    This test may be slow due to API calls and feature computation.
    """
    # Setup
    service = PredictionService()
    request = PredictionRequest(
        pair="BTC/USD",
        asset="BTCUSD",
    )

    # Execute - this will:
    # 1. Fetch real OHLCV data from Kraken
    # 2. Extract features using TA library
    # 3. Load the actual LightGBM model
    # 4. Make a real prediction
    try:
        response = service.predict(request)
    except DataFetchError as error:
        pytest.skip(
            f"Skipping live Kraken integration due to network dependency: {error}"
        )
    print(response)

    # Assert
    assert response.pair == "BTC/USD"
    assert response.asset == "BTCUSD"
    assert 0.0 <= response.probability_up <= 1.0
    assert 0.0 <= response.probability_down <= 1.0
    assert 0.0 <= response.probability_straight <= 1.0

    print(
        "\nBTC/USD Prediction: "
        f"straight={response.probability_straight:.2%} "
        f"up={response.probability_up:.2%} "
        f"down={response.probability_down:.2%}"
    )


@pytest.mark.integration
def test_predict_ethusd_live():
    """
    Live test: Fetch real data from Kraken and make prediction for ETH/USD.
    """
    # Setup
    service = PredictionService()
    request = PredictionRequest(
        pair="ETH/USD",
        asset="ETHUSD",
    )

    # Execute
    try:
        response = service.predict(request)
    except DataFetchError as error:
        pytest.skip(
            f"Skipping live Kraken integration due to network dependency: {error}"
        )

    # Assert
    assert response.pair == "ETH/USD"
    assert response.asset == "ETHUSD"
    assert 0.0 <= response.probability_up <= 1.0
    assert 0.0 <= response.probability_down <= 1.0
    assert 0.0 <= response.probability_straight <= 1.0

    print(
        "\nETH/USD Prediction: "
        f"straight={response.probability_straight:.2%} "
        f"up={response.probability_up:.2%} "
        f"down={response.probability_down:.2%}"
    )


@pytest.mark.integration
def test_predict_via_api_btcusd_live(client):
    """
    Live test: Full end-to-end test via FastAPI endpoint.

    Tests the complete HTTP request -> response cycle with real data.
    """
    # Make request to the API
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "BTC/USD",
            "asset": "BTCUSD",
        },
    )

    # Assert
    if response.status_code == 502:
        pytest.skip(
            "Skipping live API integration due to upstream Kraken network dependency"
        )

    assert response.status_code == 200
    data = response.json()

    assert data["pair"] == "BTC/USD"
    assert data["asset"] == "BTCUSD"
    assert "probability_up" in data
    assert "probability_down" in data
    assert "probability_straight" in data
    assert 0.0 <= data["probability_up"] <= 1.0
    assert 0.0 <= data["probability_down"] <= 1.0
    assert 0.0 <= data["probability_straight"] <= 1.0

    print(f"\nAPI Response: {data}")


@pytest.mark.integration
def test_predict_via_api_ethusd_live(client):
    """
    Live test: Full end-to-end test for ETH/USD via FastAPI endpoint.
    """
    # Make request
    response = client.post(
        "/api/v1/prediction/predict",
        json={
            "pair": "ETH/USD",
            "asset": "ETHUSD",
        },
    )

    # Assert
    if response.status_code == 502:
        pytest.skip(
            "Skipping live API integration due to upstream Kraken network dependency"
        )

    assert response.status_code == 200
    data = response.json()

    assert data["pair"] == "ETH/USD"
    assert data["asset"] == "ETHUSD"
    assert 0.0 <= data["probability_up"] <= 1.0
    assert 0.0 <= data["probability_down"] <= 1.0
    assert 0.0 <= data["probability_straight"] <= 1.0

    print(f"\nAPI Response: {data}")


@pytest.mark.integration
def test_predict_model_consistency():
    """
    Test that the model produces consistent results for the same input.

    Note: Results may vary slightly if Kraken data changes between calls.
    This test should be run with minimal time gap between predictions.
    """
    service = PredictionService()
    request = PredictionRequest(
        pair="BTC/USD",
        asset="BTCUSD",
    )

    # Make two predictions
    try:
        response1 = service.predict(request)
        response2 = service.predict(request)
    except DataFetchError as error:
        pytest.skip(
            f"Skipping live consistency test due to network dependency: {error}"
        )

    # Results should be very close (within 1%)
    # Small differences may occur if Kraken returns updated data
    diff = abs(response1.probability_up - response2.probability_up)
    assert diff < 0.01, f"Predictions differ by {diff:.4f}"

    print(
        "\nPrediction 1: "
        f"straight={response1.probability_straight:.4f} "
        f"up={response1.probability_up:.4f} "
        f"down={response1.probability_down:.4f}"
    )
    print(
        "Prediction 2: "
        f"straight={response2.probability_straight:.4f} "
        f"up={response2.probability_up:.4f} "
        f"down={response2.probability_down:.4f}"
    )
    print(f"Difference: {diff:.6f}")


@pytest.mark.integration
def test_prediction_service_uses_configured_model_path():
    """Regression: configured settings.model_path should resolve to existing artifact."""
    settings = get_settings()
    assert settings.model_path.exists(), (
        "Configured model artifact is missing at "
        f"{settings.model_path}. Integration prediction assumptions require a valid model file."
    )
