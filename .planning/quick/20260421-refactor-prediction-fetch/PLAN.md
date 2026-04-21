---
status: complete
---
# Plan: Refactor Prediction Fetch

**Task:** The prediction feature only needs to fetch data from my historic_data not directly to the provider with an interval setting of 60 and at least 200 candles. Keep in mind that the current kraken API is offline, so use the provided result as a template that will be returned by our historic_data API. The crypto format should be like BTC/USD or ETH/USD.

## Steps
1. Replace `DataProvider` with `HistoricDataService` in `PredictionService.__init__`.
2. Rewrite `PredictionService._fetch_historic_dataframe` to call `HistoricDataService.get_live_data` requesting 200 candles at a 60-minute interval.
3. Update `PredictionRequest` schemas to use correct `BTC/USD` format, replacing the outdated `XXBTZUSD`.
4. Update all `mock_kraken_payload` instances in `test_service.py` to match the expected `HistoricDataResponse` model format with 200 candles.
5. Fix `app/core/config.py` so that `settings.model_path` dynamically resolves to the correct path regardless of CWD.
6. Verify the entire Pytest test suite passes successfully.