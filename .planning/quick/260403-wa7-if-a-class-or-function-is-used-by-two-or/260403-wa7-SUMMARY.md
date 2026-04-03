---
phase: quick-260403-wa7
plan: 01
subsystem: api
tags: [ohlcv, kraken, refactor, decoupling, testing]
requires: []
provides:
  - shared Kraken OHLCV transport/parsing primitives in app.core
  - removal of cross-feature import coupling in prediction service
  - regression test coverage for shared OHLCV behaviors
affects: [historic-data, prediction, core-shared-utilities]
tech-stack:
  added: []
  patterns: [shared-core-module-for-reused-feature-primitives]
key-files:
  created:
    - app/core/ohlcv.py
    - tests/core/test_ohlcv.py
    - .planning/quick/260403-wa7-if-a-class-or-function-is-used-by-two-or/260403-wa7-SUMMARY.md
  modified:
    - app/features/historic_data/service.py
    - app/features/prediction/service.py
    - tests/features/historic_data/test_service.py
key-decisions:
  - "Centralize KrakenAPIClient and OHLCVDataFrame in app.core.ohlcv as the single shared source."
  - "Keep HistoricDataService focused on orchestration and response shaping; preserve endpoint behavior parity."
patterns-established:
  - "If reused by multiple features, place primitive/domain utility in app.core and import from features."
requirements-completed: [QUICK-260403-WA7]
duration: 3min
completed: 2026-04-03
---

# Phase quick-260403-wa7 Plan 01: If a class or function is used by two or more Summary

**Kraken OHLCV fetch/parsing primitives were extracted into `app.core.ohlcv` and both historic-data and prediction services now consume the shared module without cross-feature coupling.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-03T16:17:29Z
- **Completed:** 2026-04-03T16:20:20Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added TDD RED regression tests in `tests/core/test_ohlcv.py` that targeted `app.core.ohlcv` and failed before implementation due to missing module.
- Implemented shared `KrakenAPIClient` and `OHLCVDataFrame` in `app/core/ohlcv.py` with existing exception semantics.
- Updated both dependent features to import shared primitives from core, removing prediction-to-historic cross-feature coupling.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add failing shared-module regression tests first** - `41eaf18` (test)
2. **Task 2: Implement shared OHLCV module and update both feature dependents** - `9012b84` (feat)

**Plan metadata:** pending in this commit

## Files Created/Modified
- `tests/core/test_ohlcv.py` - Shared-module regression tests for transport mapping, parsing normalization, and validation errors.
- `app/core/ohlcv.py` - Shared `KrakenAPIClient` and `OHLCVDataFrame` primitives.
- `app/features/historic_data/service.py` - Reduced to orchestration, imports shared primitives from `app.core.ohlcv`.
- `app/features/prediction/service.py` - Switched shared primitive import path to `app.core.ohlcv`.
- `tests/features/historic_data/test_service.py` - Updated OHLCVDataFrame import to shared module path.

## Decisions Made
- Moved reusable OHLCV transport/parsing classes into `app.core` to enforce architecture rule: shared logic must not be owned by feature packages.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## Self-Check: PASSED

- FOUND: `.planning/quick/260403-wa7-if-a-class-or-function-is-used-by-two-or/260403-wa7-SUMMARY.md`
- FOUND: `app/core/ohlcv.py`
- FOUND: `tests/core/test_ohlcv.py`
- FOUND: Commit `41eaf18`
- FOUND: Commit `9012b84`
