"""
FastAPI router for prediction endpoints.

Endpoints:
- POST /predict: Make price movement prediction for a trading pair
"""

from fastapi import APIRouter, Depends

from app.features.prediction.schemas import PredictionRequest, PredictionResponse
from app.features.prediction.service import PredictionService

router = APIRouter()


def get_prediction_service() -> PredictionService:
    """
    Dependency injection factory for PredictionService.

    Returns:
        PredictionService instance
    """
    return PredictionService()


@router.post("/predict", response_model=PredictionResponse)
async def predict_price_movement(
    request: PredictionRequest,
    service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    """
    Predict forex price movement probability.

    Fetches 1 week of hourly OHLCV data from Kraken, extracts technical
    indicators and custom features, then uses a trained LightGBM model
    to predict the probability of upward price movement.

    Args:
        request: Trading pair and asset information
        service: Injected PredictionService instance

    Returns:
        Prediction probability for upward movement (0.0 to 1.0)

    Raises:
        502: If fetching data from Kraken fails
        422: If insufficient data or validation errors
        503: If ML model cannot be loaded
    """
    return service.predict(request)
