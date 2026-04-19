---
phase: quick
plan: 1
subsystem: api
tags: [refactor, configuration, api-client]
requires: []
provides: [dynamic-kraken-interval]
affects: [api/app/core/config.py, api/app/shared/ohlcv/kraken_api.py]
tech-stack:
  added: []
  patterns: [dependency-injection, dynamic-configuration]
key-files:
  created: []
  modified:
    - api/app/core/config.py
    - api/app/shared/ohlcv/kraken_api.py
    - api/tests/core/test_ohlcv.py
decisions:
  - Remove fixed `KRAKEN_HOURLY_INTERVAL` from global configuration to allow dynamic timeframes per request.
  - Require callers of `fetch_ohlcv_data` to explicitly provide the interval parameter to prevent implicit coupling to global fallback.
metrics:
  duration: 1m
  tasks-completed: 3/3
  started-at: "2026-04-19T00:00:00Z"
  completed-at: "2026-04-19T00:01:00Z"
---

# Phase Quick Plan 1: Update API Interval Payload Summary

Updated `KrakenAPIClient` to accept dynamic time intervals per request instead of relying on a hardcoded fallback from settings.

## Completed Tasks

1. **Remove KRAKEN_HOURLY_INTERVAL from config** - Removed static fallback variable from `Settings`.
2. **Require interval in kraken_api.py and remove fallback** - Updated `fetch_ohlcv_data` signature to make `interval` mandatory.
3. **Update tests to pass interval** - Refactored test assertions to explicitly supply the required parameter.

## Deviations from Plan

None - plan executed exactly as written.

## Threat Flags

None - No security-relevant changes were made.

## Known Stubs

None.

## Self-Check: PASSED
FOUND: api/app/core/config.py
FOUND: api/app/shared/ohlcv/kraken_api.py
FOUND: api/tests/core/test_ohlcv.py
