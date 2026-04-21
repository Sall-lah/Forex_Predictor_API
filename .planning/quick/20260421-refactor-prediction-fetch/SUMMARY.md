---
status: complete
---
# Summary: Refactor Prediction Fetch

**Changes implemented:**
- Successfully integrated `HistoricDataService` into `PredictionService` replacing the previous `DataProvider`.
- Configured the data fetch interval to 60 minutes with a minimum required sample of 200 candles, utilizing the `HistoricDataRequest` format `BTC/USD`.
- Dynamically resolved the `settings.model_path` resolving to `api/app/features/prediction/ml_models` relative to `config.py` explicitly so that `pytest` passes even from the repo root.
- Adjusted all `mock_kraken_payload` instances within the test suite to use the `HistoricDataResponse` model with populated `OHLCVRecord` instances (size: 200) instead of the previous nested dictionary format.
- Run `pytest api/tests/features/prediction` successfully, achieving 100% test pass rate!

**Completed tasks:**
- Refactored `PredictionService` data fetch internals.
- Cleaned up mock payloads and corrected test assumptions.
- Handled edge cases regarding relative vs absolute model paths in integration tests.