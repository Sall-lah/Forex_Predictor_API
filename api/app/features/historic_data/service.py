"""Service layer orchestration for historic OHLCV data retrieval."""

import logging

from app.core.config import get_settings
from app.shared.ohlcv import KrakenAPIClient, OHLCVDataFrame
from app.features.historic_data.schemas import HistoricDataResponse, OHLCVRecord

logger = logging.getLogger(__name__)
settings = get_settings()


class HistoricDataService:
    """Coordinate Kraken fetch, shared parsing, and API response formatting."""

    def __init__(self, api_client: KrakenAPIClient | None = None) -> None:
        """Initialize service with optional Kraken client dependency."""
        self.api_client = api_client or KrakenAPIClient()

    def fetch_hourly_ohlcv(self, pair: str, interval: int = 1) -> HistoricDataResponse:
        """Fetch one week of OHLCV candles for the given pair and interval."""
        payload = self.api_client.fetch_ohlcv_data(
            pair, count=settings.KRAKEN_DEFAULT_CANDLES, interval=interval
        )

        ohlcv_data = OHLCVDataFrame.from_kraken_response(payload)
        ohlcv_data.validate()

        records = [OHLCVRecord(**row) for row in ohlcv_data.to_records()]

        logger.info(
            "Fetched Kraken data for '%s' — %d candles (interval: %dm)",
            pair,
            len(records),
            interval,
        )

        return HistoricDataResponse(
            symbol=pair,
            total_records=len(records),
            data=records,
        )
