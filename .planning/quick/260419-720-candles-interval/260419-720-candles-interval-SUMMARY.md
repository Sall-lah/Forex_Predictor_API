---
phase: quick
plan: 1
subsystem: api/core/kraken
tags:
  - config
  - kraken-api
  - data-fetching
dependency_graph:
  requires: []
  provides:
    - Interval-agnostic 720 candle fetching
    - Configuration for KRAKEN_DEFAULT_CANDLES and PREDICTION_FETCH_CANDLES
  affects:
    - Historic Data Service
    - Prediction Service
tech_stack:
  added: []
  patterns: []
key_files:
  created: []
  modified:
    - api/app/core/config.py
    - api/app/shared/ohlcv/kraken_api.py
    - api/app/features/historic_data/service.py
    - api/app/features/prediction/service.py
    - api/tests/core/test_ohlcv.py
decisions:
  - "Changed `KRAKEN_DEFAULT_HOURS` to `KRAKEN_DEFAULT_CANDLES` and `PREDICTION_FETCH_HOURS` to `PREDICTION_FETCH_CANDLES` to consistently fetch 720 data points regardless of interval."
  - "Updated the Kraken API client to accept `count` instead of `hours` and compute `since` timestamp based on `now - (count * interval * 60)`."
metrics:
  duration: "5m"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 5
  date_completed: "2026-04-19"
---

# Phase Quick Plan 1: 260419-720-candles-interval Summary

Updated the Kraken API client to dynamically calculate the `since` timestamp to fetch a fixed number of candles (720) across varying intervals.

## Deviations from Plan
None - plan executed exactly as written.

## Implementation Details
1. Replaced `KRAKEN_DEFAULT_HOURS` and `PREDICTION_FETCH_HOURS` with `KRAKEN_DEFAULT_CANDLES` and `PREDICTION_FETCH_CANDLES` in `config.py` (both set to 720).
2. Modified the `KrakenAPIClient` to accept `count` in `fetch_ohlcv_data` and calculate the `since` timestamp as `now - (count * interval * 60)`.
3. Updated service layers (`HistoricDataService` and `PredictionService`) to use the new config keys and `count` parameter.
4. Addressed tests to use `count=...` instead of `hours=...`.

## Self-Check: PASSED
- `api/app/core/config.py` FOUND
- `api/app/shared/ohlcv/kraken_api.py` FOUND
- Commits found: 3c767b1