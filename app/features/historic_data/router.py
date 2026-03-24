"""
Router for the Historic Data feature.

Why keep business logic out: The router is a thin traffic controller.
It delegates all computation to HistoricDataService, which is injected
via FastAPI's Depends() so it can be swapped in tests.
"""

from fastapi import APIRouter, Depends, Query

from app.features.historic_data.schemas import (
    HistoricDataRequest,
    HistoricDataResponse,
)
from app.features.historic_data.service import HistoricDataService

router = APIRouter()


def get_historic_data_service() -> HistoricDataService:
    """
    Factory for dependency injection.

    Why a factory function: FastAPI's Depends() can call this on
    each request, making it trivial to override in tests with
    app.dependency_overrides.
    """
    return HistoricDataService()


@router.get(
    "/live",
    response_model=HistoricDataResponse,
    summary="Fetch live hourly OHLCV data from Kraken",
    description=(
        "Calls the Kraken REST API to retrieve the last 30 days of hourly "
        "OHLCV candles for the requested pair, enriches them with SMA(14), "
        "RSI(14), MACD and MACD Signal indicators, and returns the result."
    ),
)
async def get_live_data(
    pair: str = Query(
        ...,
        description="Kraken asset-pair identifier, e.g. 'XXBTZUSD' or 'ETHUSD'.",
        examples=["XXBTZUSD"],
    ),
    service: HistoricDataService = Depends(get_historic_data_service),
) -> HistoricDataResponse:
    """
    Endpoint that fetches live data from Kraken and returns enriched records.

    The service owns the HTTP call and all TA computation; this function
    only bridges HTTP ↔ domain.
    """
    return service.fetch_hourly_ohlcv(pair)


@router.post(
    "/compute-indicators",
    response_model=HistoricDataResponse,
    summary="Compute technical indicators on OHLCV data",
    description=(
        "Accepts raw OHLCV candle data and returns the same records "
        "enriched with Simple Moving Average (SMA), Relative "
        "Strength Index (RSI), MACD, and MACD_signal columns."
    ),
)
async def compute_indicators(
    request: HistoricDataRequest,
    service: HistoricDataService = Depends(get_historic_data_service),
) -> HistoricDataResponse:
    """
    Endpoint that receives OHLCV data and returns enriched records.

    The service handles all pandas/ta computation; this function
    only bridges HTTP ↔ domain.
    """
    return service.compute_indicators(request)
