"""
Live integration tests for prediction feature.

These tests make real API calls to Kraken and use the actual ML model.
They should be run sparingly to avoid rate limiting.

Run with: pytest tests/features/prediction/test_integration.py -v
"""

import pytest

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
    response = service.predict(request)
    print(response)

    # Assert
    assert response.pair == "BTC/USD"
    assert response.asset == "BTCUSD"
    assert 0.0 <= response.probability_up <= 1.0

    print(
        f"\nBTC/USD Prediction: {response.probability_up:.2%} probability of upward movement"
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
    response = service.predict(request)

    # Assert
    assert response.pair == "ETH/USD"
    assert response.asset == "ETHUSD"
    assert 0.0 <= response.probability_up <= 1.0

    print(
        f"\nETH/USD Prediction: {response.probability_up:.2%} probability of upward movement"
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
    assert response.status_code == 200
    data = response.json()

    assert data["pair"] == "BTC/USD"
    assert data["asset"] == "BTCUSD"
    assert "probability_up" in data
    assert 0.0 <= data["probability_up"] <= 1.0

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
    assert response.status_code == 200
    data = response.json()

    assert data["pair"] == "ETH/USD"
    assert data["asset"] == "ETHUSD"
    assert 0.0 <= data["probability_up"] <= 1.0

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
    response1 = service.predict(request)
    response2 = service.predict(request)

    # Results should be very close (within 1%)
    # Small differences may occur if Kraken returns updated data
    diff = abs(response1.probability_up - response2.probability_up)
    assert diff < 0.01, f"Predictions differ by {diff:.4f}"

    print(f"\nPrediction 1: {response1.probability_up:.4f}")
    print(f"Prediction 2: {response2.probability_up:.4f}")
    print(f"Difference: {diff:.6f}")
