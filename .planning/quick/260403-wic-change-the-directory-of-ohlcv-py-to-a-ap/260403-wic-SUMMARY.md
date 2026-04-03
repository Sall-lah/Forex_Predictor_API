---
phase: quick-260403-wic
plan: 01
subsystem: api
tags: [ohlcv, shared-package, kraken, refactor, import-migration]
requires: []
provides:
  - app.shared.ohlcv package split into Kraken transport and dataframe modules
  - service/test import migration from app.core.ohlcv to app.shared.ohlcv
  - removal of deprecated app/core/ohlcv.py module
affects: [historic-data, prediction, shared-utilities]
tech-stack:
  added: []
  patterns: [shared-package-boundary, transport-vs-dataframe-separation]
key-files:
  created:
    - app/shared/__init__.py
    - app/shared/ohlcv/__init__.py
    - app/shared/ohlcv/kraken_api.py
    - app/shared/ohlcv/ohlc_dataframe.py
    - .planning/quick/260403-wic-change-the-directory-of-ohlcv-py-to-a-ap/260403-wic-SUMMARY.md
  modified:
    - app/features/historic_data/service.py
    - app/features/prediction/service.py
    - tests/core/test_ohlcv.py
    - tests/features/historic_data/test_service.py
    - app/core/ohlcv.py
key-decisions:
  - "Expose KrakenAPIClient and OHLCVDataFrame through app.shared.ohlcv.__init__ to keep a stable import surface."
  - "Delete app/core/ohlcv.py after migration to enforce fail-fast on deprecated imports."
patterns-established:
  - "Shared primitives live under app/shared and are imported by feature services."
requirements-completed: [QUICK-260403-WIC]
duration: 3min
completed: 2026-04-03
---

# Phase quick-260403-wic Plan 01: Change the directory of ohlcv.py to a ap Summary

**Shared OHLCV logic now lives in `app.shared.ohlcv` with transport and DataFrame responsibilities split into dedicated modules and all feature imports rewired.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-03T16:28:06Z
- **Completed:** 2026-04-03T16:31:22Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- Completed TDD RED+GREEN for the new shared package path by first failing on `app.shared.ohlcv` import and then implementing the package.
- Split `KrakenAPIClient` and `OHLCVDataFrame` into `kraken_api.py` and `ohlc_dataframe.py` with unchanged behavior and exceptions.
- Rewired service/test imports and removed deprecated `app/core/ohlcv.py`, then re-ran targeted regression tests successfully.

## Task Commits

Each task was committed atomically:

1. **Task 1: Split `app/core/ohlcv.py` into shared Kraken and DataFrame modules** - `9b849d6` (test, RED), `246d578` (feat, GREEN)
2. **Task 2: Rewire services and tests to the new shared package path** - `82b1abb` (feat)
3. **Task 3: Enforce migration completion and remove old module** - `7582a3d` (refactor)

**Plan metadata:** pending in this commit

## Files Created/Modified
- `app/shared/ohlcv/kraken_api.py` - Kraken request construction, transport error mapping, and API envelope validation.
- `app/shared/ohlcv/ohlc_dataframe.py` - Kraken payload parsing, incomplete-candle handling, and OHLCV validation/record conversion.
- `app/shared/ohlcv/__init__.py` - Stable re-export surface for shared imports.
- `app/features/historic_data/service.py` - Imports shared primitives from `app.shared.ohlcv`.
- `app/features/prediction/service.py` - Imports shared primitives from `app.shared.ohlcv`.
- `tests/core/test_ohlcv.py` - Regression tests now target the shared package path.
- `tests/features/historic_data/test_service.py` - OHLCVDataFrame import updated to shared package path.
- `app/core/ohlcv.py` - Removed after migration completion.

## Decisions Made
- Enforced `app.shared.ohlcv` as the single import boundary for shared OHLCV logic to keep feature modules decoupled from implementation layout.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## Self-Check: PASSED

- FOUND: `.planning/quick/260403-wic-change-the-directory-of-ohlcv-py-to-a-ap/260403-wic-SUMMARY.md`
- FOUND: `app/shared/ohlcv/kraken_api.py`
- FOUND: `app/shared/ohlcv/ohlc_dataframe.py`
- FOUND: `app/shared/ohlcv/__init__.py`
- FOUND: deletion confirmed for `app/core/ohlcv.py`
- FOUND: Commit `9b849d6`
- FOUND: Commit `246d578`
- FOUND: Commit `82b1abb`
- FOUND: Commit `7582a3d`
