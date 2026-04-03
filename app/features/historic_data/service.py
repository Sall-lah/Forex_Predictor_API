"""Service layer orchestration for historic OHLCV data retrieval."""

import logging

from app.core.config import get_settings
from app.core.ohlcv import KrakenAPIClient, OHLCVDataFrame
from app.features.historic_data.schemas import HistoricDataResponse, OHLCVRecord

logger = logging.getLogger(__name__)
settings = get_settings()


class HistoricDataService:
    """Coordinate Kraken fetch, shared parsing, and API response formatting."""

    def __init__(self, api_client: KrakenAPIClient | None = None) -> None:
        """Initialize service with optional Kraken client dependency."""
        self.api_client = api_client or KrakenAPIClient()

    def fetch_hourly_ohlcv(self, pair: str) -> HistoricDataResponse:
        """Fetch one week of hourly OHLCV candles for the given pair."""
        payload = self.api_client.fetch_ohlcv_data(pair, settings.KRAKEN_DEFAULT_HOURS)

        ohlcv_data = OHLCVDataFrame.from_kraken_response(payload)
        ohlcv_data.validate()

        records = [OHLCVRecord(**row) for row in ohlcv_data.to_records()]

        logger.info(
            "Fetched Kraken data for '%s' — %d hourly candles",
            pair,
            len(records),
        )

        return HistoricDataResponse(
            symbol=pair,
            total_records=len(records),
            data=records,
        )
