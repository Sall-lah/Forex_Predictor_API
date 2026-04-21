"""Service layer orchestration for historic OHLCV data retrieval."""

import logging

# from app.core.exceptions import DataFetchError, DataValidationError, InsufficientDataError
from app.features.historic_data.schemas import HistoricDataRequest, HistoricDataResponse, OHLCVRecord
from app.shared.ohlcv import OHLCVDataFrame, DataProvider, get_provider

logger = logging.getLogger(__name__)


class HistoricDataService:
    """Coordinates Historic Data workflows."""

    def __init__(self, api_client: DataProvider | None = None) -> None:
        """Inject dependencies or instantiate defaults."""
        self.api_client = api_client or get_provider()

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
            "Fetched data for '%s' — %d candles (interval: %dm)",
            request.pair,
            len(records),
            request.interval,
        )

        return HistoricDataResponse(
            symbol=request.pair,
            total_records=len(records),
            data=records,
        )
