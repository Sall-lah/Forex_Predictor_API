---
phase: quick
plan: 260419-h5i
subsystem: web
tags: [frontend, swr, ui, sync-spinner]
dependency_graph:
  requires: []
  provides: [sync-spinner-ui-update]
  affects: [web/src/hooks/useMarketData.ts, web/src/pages/Dashboard.tsx]
tech_stack:
  added: []
  patterns: [swr-data-fetching]
key_files:
  created: []
  modified:
    - web/src/hooks/useMarketData.ts
    - web/src/pages/Dashboard.tsx
decisions:
  - "Changed sync spinner condition to check `isLoading` instead of `isValidating` to prevent blinking on background revalidation."
metrics:
  duration: 1m
  completed_date: "2026-04-19"
---

# Phase quick Plan 260419-h5i: Only display sync spinner when changing interval Summary

Updated the sync spinner in the dashboard to use SWR's `isLoading` state rather than `isValidating`, ensuring the spinner only appears during initial data fetch or interval change rather than background polling.

## Summary of Changes

- **web/src/hooks/useMarketData.ts**: Extracted `isLoading` from `useSWR` and returned it along with the rest of the market data.
- **web/src/pages/Dashboard.tsx**: Replaced the `isValidating` check with `isLoading` in the sync spinner condition and removed the unused `isValidating` variable.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED
- `web/src/hooks/useMarketData.ts` updated
- `web/src/pages/Dashboard.tsx` updated
- Commit: ec8bfd0
