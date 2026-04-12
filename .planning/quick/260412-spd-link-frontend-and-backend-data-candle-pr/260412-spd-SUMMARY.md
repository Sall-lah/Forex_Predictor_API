---
phase: quick
plan: 1
subsystem: frontend
tags: [hooks, market-data, api-fetch]
requires: []
provides: [fixed-historic-data-fetch]
affects: [web/src/hooks/useMarketData.ts]
tech-stack:
  added: []
  patterns: [react-hooks, default-parameters]
key-files:
  created: []
  modified:
    - web/src/hooks/useMarketData.ts
decisions:
  - Add optional `pair` string argument to `useMarketData` hook with a default value of `'BTC/USD'`.
  - Append `pair` as a query parameter in the historic-data fetch URL to avoid 422 errors from the backend.
  - Add `pair` to the `useEffect` dependency array.
metrics:
  duration: 1m
  tasks_completed: 1
  files_modified: 1
---

# Quick Plan 1: link frontend and backend data candle Summary

The frontend fetching logic has been fixed to send the required `pair` query parameter. The `useMarketData` hook now accepts an optional `pair` parameter (defaulting to `'BTC/USD'`), encodes it, and includes it in the `/api/v1/historic-data/live` fetch request. This resolves the 422 Validation Error previously encountered.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None found.

## Self-Check: PASSED
FOUND: web/src/hooks/useMarketData.ts
FOUND: eb6a707
