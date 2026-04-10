"""
API routes for Historic Data feature.

Endpoints:
- GET /live: Fetch live OHLCV data from Kraken
"""

from fastapi import APIRouter, Depends, Query

from app.features.historic_data.schemas import HistoricDataResponse
from app.features.historic_data.service import HistoricDataService

router = APIRouter()


def get_service() -> HistoricDataService:
    """
    Dependency injection factory for HistoricDataService.

    Returns:
        New HistoricDataService instance
    """
    return HistoricDataService()


@router.get(
    "/live",
    response_model=HistoricDataResponse,
    summary="Fetch live hourly OHLCV data from Kraken",
    description=(
        "Retrieves 1 week (168 hours) of hourly OHLCV candles from Kraken API. "
        "Returns timestamp, open, high, low, close, and volume data."
    ),
)
async def get_live_data(
    pair: str = Query(
        ...,
        description="Kraken trading pair (e.g., 'BTC/UDS', 'ETH/USD')",
        examples=["BTC/USD"],
    ),
    service: HistoricDataService = Depends(get_service),
) -> HistoricDataResponse:
    """
    Fetch live OHLCV data from Kraken.

    Args:
        pair: Kraken asset pair identifier
        service: Injected service instance

    Returns:
        Response with OHLCV records
    """
    return service.fetch_hourly_ohlcv(pair)
