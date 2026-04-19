---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - api/app/shared/ohlcv/ohlc_dataframe.py
  - api/app/features/historic_data/service.py
  - api/tests/core/test_ohlcv.py
  - api/tests/features/historic_data/test_service.py
autonomous: true
requirements: [QUICK-01]
must_haves:
  truths:
    - Historic data endpoint returns the current unfinished candle.
    - Prediction endpoint retains default behavior (drops unfinished candle).
  artifacts:
    - path: api/app/shared/ohlcv/ohlc_dataframe.py
      provides: from_kraken_response method with drop_unfinished_candle parameter
    - path: api/app/features/historic_data/service.py
      provides: Passing drop_unfinished_candle=False in OHLCVDataFrame.from_kraken_response call
  key_links: []
---

<objective>
Modify the OHLCV DataFrame parsing logic to optionally keep the latest (unfinished) candle from the Kraken API response. Ensure the historic data endpoint includes this candle while preserving the prediction endpoint's current behavior of dropping it.
Purpose: Provides complete recent data for historic charting without breaking the prediction model's need for only finished candles.
Output: Updated DataFrame parser, updated historic data service, and passing tests.
</objective>

<execution_context>
This is a quick fix executed in a single plan.
</execution_context>

<context>
@api/app/shared/ohlcv/ohlc_dataframe.py
@api/app/features/historic_data/service.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add parameter to OHLCVDataFrame</name>
  <files>api/app/shared/ohlcv/ohlc_dataframe.py, api/tests/core/test_ohlcv.py</files>
  <action>Modify `OHLCVDataFrame.from_kraken_response` to accept a boolean parameter `drop_unfinished_candle: bool = True`. Update the logic that drops the last row (e.g. `df = df.iloc[:-1]`) to only happen if `drop_unfinished_candle` is True. Add a test in `test_ohlcv.py` to assert that when `drop_unfinished_candle=False`, the last row is retained.</action>
  <verify>
    <automated>pytest api/tests/core/test_ohlcv.py</automated>
  </verify>
  <done>OHLCV DataFrame can optionally retain the unfinished candle, and tests cover both True and False cases.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Update HistoricDataService to keep unfinished candles</name>
  <files>api/app/features/historic_data/service.py, api/tests/features/historic_data/test_service.py</files>
  <action>Update the call to `OHLCVDataFrame.from_kraken_response(payload)` in `HistoricDataService` to pass `drop_unfinished_candle=False`. Update the relevant unit tests in `test_service.py` to expect the response length not to be truncated by 1, or to match the modified mock behavior if affected.</action>
  <verify>
    <automated>pytest api/tests/features/historic_data/test_service.py</automated>
  </verify>
  <done>HistoricDataService explicitly requests keeping the unfinished candle, and tests pass.</done>
</task>

</tasks>

<verification>
pytest api/tests/
</verification>

<success_criteria>
- `OHLCVDataFrame.from_kraken_response` signature accepts `drop_unfinished_candle=True` by default.
- `HistoricDataService` uses `drop_unfinished_candle=False`.
- `PredictionService` is untouched and uses the default.
- All unit tests pass.
</success_criteria>

<output>
After completion, proceed to execution via GSD or test suites.
</output>
