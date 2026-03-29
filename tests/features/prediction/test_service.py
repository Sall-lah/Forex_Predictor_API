"""
Unit tests for PredictionService with mocked dependencies.

Tests:
- Successful prediction flow
- Kraken API fetch errors
- Insufficient data errors
- Model loading errors
- Feature extraction errors
"""

from unittest.mock import Mock, MagicMock
import pandas as pd
import pytest

from app.core.exceptions import (
    DataFetchError,
    InsufficientDataError,
    ModelNotLoadedError,
)
from app.features.prediction.schemas import PredictionRequest, PredictionResponse
from app.features.prediction.service import (
    PredictionService,
    OHLCVPreprocessor,
    ModelLoader,
)


def test_predict_success(mocker):
    """Test successful prediction workflow with all components mocked."""
    # Setup
    service = PredictionService()

    # Mock request
    request = PredictionRequest(pair="XXBTZUSD", asset="BTCUSD")

    # Mock Kraken API response
    mock_kraken_payload = {
        "error": [],
        "result": {
            "XXBTZUSD": [
                [
                    1711000000,
                    "50000.0",
                    "51000.0",
                    "49000.0",
                    "50500.0",
                    "50200.0",
                    "100.5",
                    150,
                ],
            ]
            * 200,  # 200 rows to ensure enough data
            "last": 1711000000,
        },
    }

    mock_api_client = mocker.patch.object(service.api_client, "fetch_ohlcv_data")
    mock_api_client.return_value = mock_kraken_payload

    # Mock preprocessor - return DataFrame with required features
    mock_features_df = pd.DataFrame(
        {
            "ema_9": [50000.0],
            "ema_21": [49800.0],
            "rsi_14h": [55.0],
            "volume": [100.0],
            "asset": ["BTCUSD"],
            # Add minimal feature set (in reality would have 49 features)
        }
    )

    mock_preprocessor = mocker.patch.object(service.preprocessor, "extract_features")
    mock_preprocessor.return_value = mock_features_df

    # Mock model loader and prediction
    mock_model = Mock()
    mock_model.predict_proba.return_value = [[0.35, 0.65]]  # 65% probability up

    # Mock the singleton's get_model method
    mocker.patch.object(ModelLoader, "get_model", return_value=mock_model)

    # Execute
    response = service.predict(request)

    # Assert
    assert isinstance(response, PredictionResponse)
    assert response.pair == "XXBTZUSD"
    assert response.asset == "BTCUSD"
    assert response.probability_up == 0.65

    # Verify method calls
    mock_api_client.assert_called_once()
    mock_preprocessor.assert_called_once()
    mock_model.predict_proba.assert_called_once()


def test_predict_kraken_api_error(mocker):
    """Test handling of Kraken API fetch error."""
    # Setup
    service = PredictionService()
    request = PredictionRequest(pair="XXBTZUSD", asset="BTCUSD")

    # Mock API client to raise error
    mock_api_client = mocker.patch.object(service.api_client, "fetch_ohlcv_data")
    mock_api_client.side_effect = DataFetchError("Kraken API unreachable")

    # Execute & Assert
    with pytest.raises(DataFetchError) as exc_info:
        service.predict(request)

    assert "Kraken API unreachable" in str(exc_info.value)


def test_predict_insufficient_data(mocker):
    """Test handling of insufficient data for feature extraction."""
    # Setup
    service = PredictionService()
    request = PredictionRequest(pair="XXBTZUSD", asset="BTCUSD")

    # Mock Kraken API with minimal data
    mock_kraken_payload = {
        "error": [],
        "result": {
            "XXBTZUSD": [
                [
                    1711000000,
                    "50000.0",
                    "51000.0",
                    "49000.0",
                    "50500.0",
                    "50200.0",
                    "100.5",
                    150,
                ],
            ]
            * 10,  # Only 10 rows - insufficient
            "last": 1711000000,
        },
    }

    mock_api_client = mocker.patch.object(service.api_client, "fetch_ohlcv_data")
    mock_api_client.return_value = mock_kraken_payload

    # Preprocessor should raise InsufficientDataError
    mock_preprocessor = mocker.patch.object(service.preprocessor, "extract_features")
    mock_preprocessor.side_effect = InsufficientDataError("Need at least 168 rows")

    # Execute & Assert
    with pytest.raises(InsufficientDataError) as exc_info:
        service.predict(request)

    assert "168" in str(exc_info.value)


def test_predict_model_not_loaded(mocker):
    """Test handling of ML model loading failure."""
    # Setup
    service = PredictionService()
    request = PredictionRequest(pair="XXBTZUSD", asset="BTCUSD")

    # Mock successful data fetch and preprocessing
    mock_kraken_payload = {
        "error": [],
        "result": {
            "XXBTZUSD": [
                [
                    1711000000,
                    "50000.0",
                    "51000.0",
                    "49000.0",
                    "50500.0",
                    "50200.0",
                    "100.5",
                    150,
                ],
            ]
            * 200,
            "last": 1711000000,
        },
    }

    mock_api_client = mocker.patch.object(service.api_client, "fetch_ohlcv_data")
    mock_api_client.return_value = mock_kraken_payload

    mock_features_df = pd.DataFrame(
        {
            "ema_9": [50000.0],
            "volume": [100.0],
        }
    )

    mock_preprocessor = mocker.patch.object(service.preprocessor, "extract_features")
    mock_preprocessor.return_value = mock_features_df

    # Mock model loader to raise error
    mocker.patch.object(
        ModelLoader,
        "get_model",
        side_effect=ModelNotLoadedError("Model file not found"),
    )

    # Execute & Assert
    with pytest.raises(ModelNotLoadedError) as exc_info:
        service.predict(request)

    assert "Model file not found" in str(exc_info.value)


def test_predict_feature_extraction_error(mocker):
    """Test handling of feature extraction errors."""
    # Setup
    service = PredictionService()
    request = PredictionRequest(pair="XXBTZUSD", asset="BTCUSD")

    # Mock successful data fetch
    mock_kraken_payload = {
        "error": [],
        "result": {
            "XXBTZUSD": [
                [
                    1711000000,
                    "50000.0",
                    "51000.0",
                    "49000.0",
                    "50500.0",
                    "50200.0",
                    "100.5",
                    150,
                ],
            ]
            * 200,
            "last": 1711000000,
        },
    }

    mock_api_client = mocker.patch.object(service.api_client, "fetch_ohlcv_data")
    mock_api_client.return_value = mock_kraken_payload

    # Mock preprocessor to raise error
    mock_preprocessor = mocker.patch.object(service.preprocessor, "extract_features")
    mock_preprocessor.side_effect = InsufficientDataError("All rows contained NaN")

    # Execute & Assert
    with pytest.raises(InsufficientDataError) as exc_info:
        service.predict(request)

    assert "NaN" in str(exc_info.value)


def test_predict_different_asset(mocker):
    """Test prediction for ETHUSD asset."""
    # Setup
    service = PredictionService()
    request = PredictionRequest(pair="XETHZUSD", asset="ETHUSD")

    # Mock all dependencies
    mock_kraken_payload = {
        "error": [],
        "result": {
            "XETHZUSD": [
                [
                    1711000000,
                    "3000.0",
                    "3100.0",
                    "2900.0",
                    "3050.0",
                    "3020.0",
                    "500.5",
                    250,
                ],
            ]
            * 200,
            "last": 1711000000,
        },
    }

    mock_api_client = mocker.patch.object(service.api_client, "fetch_ohlcv_data")
    mock_api_client.return_value = mock_kraken_payload

    mock_features_df = pd.DataFrame(
        {
            "ema_9": [3000.0],
            "asset": ["ETHUSD"],
        }
    )

    mock_preprocessor = mocker.patch.object(service.preprocessor, "extract_features")
    mock_preprocessor.return_value = mock_features_df

    mock_model = Mock()
    mock_model.predict_proba.return_value = [[0.55, 0.45]]  # 45% probability up

    mocker.patch.object(ModelLoader, "get_model", return_value=mock_model)

    # Execute
    response = service.predict(request)

    # Assert
    assert response.pair == "XETHZUSD"
    assert response.asset == "ETHUSD"
    assert response.probability_up == 0.45

    # Verify preprocessor was called with correct asset
    mock_preprocessor.assert_called_once()
    call_args = mock_preprocessor.call_args
    assert call_args[0][1] == "ETHUSD"
