---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - api/app/core/config.py
  - api/app/shared/ohlcv/kraken_api.py
  - api/tests/core/test_ohlcv.py
  - api/tests/features/historic_data/test_service.py
autonomous: true
requirements: [QUICK-TASK]
must_haves:
  truths:
    - KRAKEN_HOURLY_INTERVAL is removed from configuration
    - fetch_ohlcv_data requires an interval parameter and uses it
  artifacts:
    - path: api/app/core/config.py
      provides: updated settings
    - path: api/app/shared/ohlcv/kraken_api.py
      provides: updated fetch_ohlcv_data signature
  key_links:
    - from: api/app/shared/ohlcv/kraken_api.py
      to: api/app/core/config.py
      pattern: settings\.KRAKEN_HOURLY_INTERVAL
---

<objective>
Update the API interval payload so that it dynamically uses the requested interval time instead of relying on a fixed `KRAKEN_HOURLY_INTERVAL`.
</objective>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Remove KRAKEN_HOURLY_INTERVAL from config</name>
  <files>api/app/core/config.py</files>
  <action>
    Remove `KRAKEN_HOURLY_INTERVAL: int = 60` from the `Settings` class.
  </action>
  <verify>
    <automated>grep -q "KRAKEN_HOURLY_INTERVAL" api/app/core/config.py || exit 0</automated>
  </verify>
  <done>KRAKEN_HOURLY_INTERVAL is no longer present in Settings.</done>
</task>

<task type="auto">
  <name>Task 2: Require interval in kraken_api.py and remove fallback</name>
  <files>api/app/shared/ohlcv/kraken_api.py</files>
  <action>
    Update `KrakenAPIClient.fetch_ohlcv_data` signature to make `interval: int` required (remove `| None = None`).
    Remove `interval = interval or settings.KRAKEN_HOURLY_INTERVAL`.
    Pass the interval directly to `_build_query_params`.
  </action>
  <verify>
    <automated>grep -q "interval = interval or settings.KRAKEN_HOURLY_INTERVAL" api/app/shared/ohlcv/kraken_api.py || exit 0</automated>
  </verify>
  <done>fetch_ohlcv_data requires an interval parameter and does not use the old config fallback.</done>
</task>

<task type="auto">
  <name>Task 3: Update tests to pass interval</name>
  <files>api/tests/core/test_ohlcv.py, api/tests/features/historic_data/test_service.py</files>
  <action>
    Update calls to `fetch_ohlcv_data` in tests to include an explicit `interval` parameter. For example, in `test_fetch_ohlcv_data_maps_transport_failures_to_data_fetch_error` change `client.fetch_ohlcv_data(pair="XXBTZUSD", hours=24)` to include `interval=60`. Make sure all tests pass.
  </action>
  <verify>
    <automated>pytest api/tests/core/test_ohlcv.py api/tests/features/historic_data/test_service.py</automated>
  </verify>
  <done>All tests are updated and pass.</done>
</task>

</tasks>
