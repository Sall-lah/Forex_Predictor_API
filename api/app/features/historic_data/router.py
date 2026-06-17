"""
API routes for Historic Data feature.

Endpoints:
- GET /live: Fetch live OHLCV data from Kraken
"""

from fastapi import APIRouter, Depends, Query

from app.features.historic_data.schemas import HistoricDataRequest, HistoricDataResponse
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
        description="Data trading pair (e.g., 'BTC/USD', 'ETH/USD')",
        examples=["BTC/USD"],
    ),
    interval: int = Query(
        60,
        description="Time frame interval in minutes",
        enum=[1, 5, 15, 30, 60, 240, 1440, 10080, 21600],
    ),
    count: int = Query(
        180,
        description="Number of OHLCV records to fetch",
    ),
    service: HistoricDataService = Depends(get_service),
) -> HistoricDataResponse:
    """
    Fetch live OHLCV data from Kraken.

    Args:
        pair: Kraken asset pair identifier
        interval: Time frame interval in minutes (default 60)
        service: Injected service instance

    Returns:
        Response with OHLCV records
    """
    request = HistoricDataRequest(pair=pair, interval=interval, count=count)
    return await service.get_live_data(request)
