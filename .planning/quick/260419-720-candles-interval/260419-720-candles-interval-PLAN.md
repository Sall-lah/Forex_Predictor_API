---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - api/app/core/config.py
  - api/app/shared/ohlcv/kraken_api.py
  - api/app/features/historic_data/service.py
  - api/app/features/prediction/service.py
  - api/tests/core/test_ohlcv.py
autonomous: true
requirements:
  - QUICK-01
must_haves:
  truths:
    - Kraken OHLCV API is called with a `since` timestamp calculating back 720 candles based on the requested interval.
    - `hours` parameters are replaced by `count` or `candles`.
  artifacts:
    - path: api/app/shared/ohlcv/kraken_api.py
      provides: Updated API payload calculating interval dynamic time
    - path: api/app/core/config.py
      provides: Configuration for 720 candles
  key_links:
    - from: api/app/features/historic_data/service.py
      to: api/app/shared/ohlcv/kraken_api.py
      via: fetch_ohlcv_data
---

<objective>
Update the data fetching logic to always fetch 720 candles for any interval instead of a fixed number of hours.

Purpose: Ensures that when users change timeframe intervals on the frontend, they get a consistent amount of data (e.g. 720 candles) whether the interval is 1m, 1h, or 1d.
Output: Updated configuration, Kraken API client, feature services, and tests.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update API Client and Config to use Candles instead of Hours</name>
  <files>
    api/app/core/config.py
    api/app/shared/ohlcv/kraken_api.py
    api/app/features/historic_data/service.py
    api/app/features/prediction/service.py
    api/tests/core/test_ohlcv.py
  </files>
  <action>
    1. In `api/app/core/config.py`, change `KRAKEN_DEFAULT_HOURS` to `KRAKEN_DEFAULT_CANDLES` (default 720) and `PREDICTION_FETCH_HOURS` to `PREDICTION_FETCH_CANDLES` (default 720). Also update any references in comments/tests.
    2. In `api/app/shared/ohlcv/kraken_api.py`, change `fetch_ohlcv_data` and `_build_query_params` parameter from `hours` to `count`. Update `_calculate_since_timestamp(count: int, interval: int)` to compute the `since` timestamp as `now - (count * interval * 60)`.
    3. In `api/app/features/historic_data/service.py`, replace `settings.KRAKEN_DEFAULT_HOURS` with `settings.KRAKEN_DEFAULT_CANDLES` when calling `fetch_ohlcv_data`. Note that the `interval` needs to be passed explicitly to `fetch_ohlcv_data` as a named or positional arg according to the updated signature.
    4. In `api/app/features/prediction/service.py`, replace `settings.PREDICTION_FETCH_HOURS` with `settings.PREDICTION_FETCH_CANDLES` when calling `fetch_ohlcv_data`.
    5. In `api/tests/core/test_ohlcv.py`, update `client.fetch_ohlcv_data(pair="XXBTZUSD", hours=24, interval=60)` to use `count=...`.
  </action>
  <verify>
    <automated>pytest api/tests/core/test_ohlcv.py</automated>
  </verify>
  <done>Kraken API client correctly requests 720 candles based on the interval dynamic calculation.</done>
</task>

<task type="auto">
  <name>Task 2: Ensure Tests Pass</name>
  <files>
    api/tests/features/historic_data/test_service.py
    api/tests/features/prediction/test_service.py
  </files>
  <action>
    Review existing tests for `historic_data` and `prediction`. Since we only mock `fetch_ohlcv_data` and its `kwargs`, it should not fail unless tests strictly mock the method signature or validate the returned size strictly against the number of hours. If any assertions hardcode sizes or parameters that change from `hours` to `count` / `CANDLES`, update them.
  </action>
  <verify>
    <automated>pytest api/tests/</automated>
  </verify>
  <done>All tests in the API module pass successfully.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| External API -> Backend | Data from Kraken API could potentially be malformed. Validation relies on Pydantic models. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-quick-01 | Tampering | kraken_api.py | mitigate | `OHLCVDataFrame` validation ensures returned payloads have minimum required columns and rows regardless of requested count. |
</threat_model>

<verification>
Run `pytest api/tests/` to confirm that all tests still pass and the signature changes are properly wired up.
</verification>

<success_criteria>
- Kraken fetch `since` timestamps accurately adjust to fetch 720 candles regardless of `interval`.
- No lingering `hours` hardcoded math in `kraken_api.py`.
- Automated tests pass.
</success_criteria>

<output>
After completion, create `.planning/quick/260419-720-candles-interval/quick-1-SUMMARY.md`
</output>
