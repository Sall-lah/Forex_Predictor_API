---
phase: quick
plan: 260419-frontend-backend-interval
subsystem: Fullstack
tags:
  - interval
  - frontend
  - backend
  - kraken-api
requires: []
provides:
  - dynamic interval selection across stack
affects:
  - api/app/shared/ohlcv/kraken_api.py
  - api/app/features/historic_data/router.py
  - api/app/features/historic_data/service.py
  - api/app/features/prediction/schemas.py
  - web/src/pages/Dashboard.tsx
  - web/src/hooks/useMarketData.ts
key-decisions:
  - Updated all interval defaults from 60 to 1
  - Expanded frontend selector to support full set of Kraken timeframe intervals
completed-date: 2026-04-19
duration: "5m"
---

# Quick Task 260419-frontend-backend-interval Summary

Dynamic interval selection implemented across the frontend and backend, defaulting to 1 minute.

## Execution Details

1. Backend: Checked and verified that `kraken_api.py`, router, and service methods accept the `interval` parameter. Updated the default value from `60` to `1` consistently.
2. Frontend: Located the `Dashboard.tsx` view and expanded the interval timeframe selector options to match the Kraken API accepted values (1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W, 15D). Also updated the default state in `useMarketData` and `Dashboard.tsx` to `1`.

## Deviations from Plan

None - the backend already had the interval parameter piped through from a prior task, so I focused on adding the correct defaults and expanding the frontend options list.

## Self-Check: PASSED
- `api/app/shared/ohlcv/kraken_api.py` and service layers successfully patched to default interval 1
- `web/src/pages/Dashboard.tsx` expanded dropdown mapping
- Code committed successfully.
