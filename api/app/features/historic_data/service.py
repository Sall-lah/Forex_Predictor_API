"""Service layer orchestration for historic OHLCV data retrieval."""

import logging

from app.core.config import get_settings
from app.shared.ohlcv import KrakenProvider, OHLCVDataFrame

logger = logging.getLogger(__name__)


class HistoricDataService:
    """Coordinates Historic Data workflows."""

    def __init__(self, api_client: KrakenProvider | None = None) -> None:
        """Inject dependencies or instantiate defaults."""
        self.api_client = api_client or KrakenProvider()

    def get_live_data(
        self, request: HistoricDataRequest
    ) -> HistoricDataResponse:
        """Fetch, normalize, and return recent OHLCV data."""
        logger.info(f"Fetching {request.count} periods for {request.pair}")

        payload = self.api_client.fetch_ohlcv_data(
            pair=request.pair,
            count=request.count,
            interval=request.interval,
        )

        ohlcv_data = OHLCVDataFrame.from_provider_response(payload)
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
