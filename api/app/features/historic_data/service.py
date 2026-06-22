"""Service layer orchestration for historic OHLCV data retrieval."""

from app.core.base import BaseService
from app.features.historic_data.schemas import HistoricDataRequest, HistoricDataResponse, OHLCVRecord
from app.shared.ohlcv import OHLCVDataFrame, KrakenRepository


class HistoricDataService(BaseService):
    """Coordinates Historic Data workflows."""

    def __init__(self, api_client: KrakenRepository | None = None) -> None:
        """Inject dependencies or instantiate defaults."""
        super().__init__()
        self.api_client = api_client or KrakenRepository()

    async def get_live_data(
        self, request: HistoricDataRequest
    ) -> HistoricDataResponse:
        """Fetch, normalize, and return recent OHLCV data."""
        self.logger.info(f"Fetching {request.count} periods for {request.pair}")

        payload = await self.api_client.fetch_ohlcv_data(
            pair=request.pair,
            count=request.count,
            interval=request.interval,
        )

        ohlcv_data = OHLCVDataFrame.from_provider_response(payload)
        ohlcv_data.validate()

        records = [OHLCVRecord(**row) for row in ohlcv_data.to_records()]

        self.logger.info(
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
