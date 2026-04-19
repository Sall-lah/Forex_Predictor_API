---
phase: quick
plan: 1
subsystem: react-frontend
tags:
  - refactor
  - hooks
  - swr
  - lightweight-charts
dependency_graph:
  requires:
    - REFACTOR-REACT-NO-USEEFFECT
  provides:
    - Data fetching logic
    - UI component logic
tech_stack:
  added:
    - swr
  patterns:
    - Callback Ref pattern for initialization
key_files:
  created: []
  modified:
    - web/package.json
    - web/src/hooks/useMarketData.ts
    - web/src/components/Chart.tsx
key_decisions:
  - Switched from useEffect to swr for data fetching
  - Switched to useCallback ref pattern for chart rendering
metrics:
  duration: 1m
  tasks_completed: 2
  tasks_total: 2
  completed_at: 2026-04-19T00:00:00Z
---

# Quick Plan 1: Refactor React so it does not use any useEffect Summary

## Objective
Refactor the React codebase so it does not use `useEffect` anywhere, replacing data fetching with SWR and chart lifecycle with the callback ref pattern.

## Execution Details
- Task 1: Installed `swr` and updated `useMarketData` hook to rely on `useSWR` for polling instead of a recursive `setInterval` wrapped in `useEffect`.
- Task 2: Replaced chart component container initialization and data rendering logic by utilizing the `useCallback` ref and a plain react rendering cycle instead of `useEffect`.

## Deviations from Plan
None - plan executed exactly as written.

## Self-Check: PASSED
- [x] web/package.json modified and committed.
- [x] web/src/hooks/useMarketData.ts modified and committed.
- [x] web/src/components/Chart.tsx modified and committed.
