---
phase: 01-api-updates
plan: 01
type: execute
wave: 1
subsystem: api
tags:
  - backend
  - api-params
  - kraken
  - features
dependency_graph:
  requires:
    - none
  provides:
    - Dynamic timeframe (interval) support for historic and prediction endpoints
  affects:
    - Historic Data fetching logic
    - Prediction feature extraction baseline
tech_stack:
  added: []
  patterns:
    - Pydantic Literal validation for enum types
    - Query parameter enums in FastAPI
key_files:
  created: []
  modified:
    - api/app/features/historic_data/router.py
    - api/app/features/historic_data/service.py
    - api/app/features/prediction/schemas.py
    - api/app/features/prediction/service.py
    - api/app/shared/ohlcv/kraken_api.py
key_decisions:
  - Validated interval parameters strictly against allowed Kraken timeframes using Literal/Enum
  - Preserved default 60-minute interval backward compatibility
metrics:
  duration: 10
  completed_date: "2026-04-12"
---

# Phase 01 Plan 01: API Updates for Timeframe Intervals Summary

Added dynamic timeframe interval support to Kraken OHLCV fetches across the API stack.

## Tasks Completed

### Task 1: Add interval schemas and update KrakenAPIClient
- Modified `PredictionRequest` to strictly validate `interval` using Pydantic's `Literal` type rather than just documenting it.
- Updated `KrakenAPIClient.fetch_ohlcv_data` and query building to accept and forward the interval parameter.
- **Commit:** `c33d494`

### Task 2: Wire interval through services and routers
- Exposed `interval` query parameter on `GET /api/v1/historic-data/live` with validation rules.
- Wired the parameter vertically through `HistoricDataService` to the Kraken client.
- Modified `PredictionService` to unpack the `interval` from `PredictionRequest` and forward it correctly.
- **Commit:** `0b8dacf`

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- Automated tests passed for routers, services, and the Kraken client.
- Schemas strictly validate interval values to avoid upstream Kraken rejection.
- Interval defaults to 60 for safe backward compatibility with existing ML models.

## Self-Check: PASSED
- FOUND: api/app/features/prediction/schemas.py
- FOUND: c33d494
- FOUND: 0b8dacf
