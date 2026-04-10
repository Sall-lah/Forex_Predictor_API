---
phase: 01-app-boundary-migration-backend-parity
plan: 01
subsystem: api
tags: [fastapi, monorepo, pytest]

# Dependency graph
requires: []
provides:
  - api-scoped FastAPI backend package and runtime manifests
  - api-local test suite running against moved backend
affects:
  - phase-02-env-ownership
  - phase-03-workflows-ci

# Tech tracking
tech-stack:
  added: []
  patterns: ["api/ owns backend app/tests/runtime manifests"]

key-files:
  created:
    - api/app/main.py
    - api/requirements.txt
    - api/environment.yml
    - api/pytest.ini
    - api/tests/conftest.py
  modified:
    - api/tests/features/prediction/test_router.py

key-decisions:
  - "Keep python package name as app.* while relocating under api/ for uvicorn app.main:app compatibility"

patterns-established:
  - "Run backend from api/ with api/tests as the local regression suite"

requirements-completed: [STRU-01, STRU-02, PAR-01]

# Metrics
duration: 5min
completed: 2026-04-11
---

# Phase 1 Plan 01: App Boundary Migration & Backend Parity Summary

**FastAPI backend and tests now live under api/ with preserved /health and /api/v1 behavior, verified by api-local pytest.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-11T01:01:00Z
- **Completed:** 2026-04-11T01:06:18Z
- **Tasks:** 3
- **Files modified:** 53

## Accomplishments
- Relocated the FastAPI backend package and runtime manifests into api/ with the same app entrypoint.
- Migrated all backend tests into api/tests and kept router fixtures intact for api-local runs.
- Removed root-level backend copies and confirmed api-local regression suite passes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Move the backend application tree into api/** - `430d20f` (chore)
2. **Task 2: Relocate backend tests into api/ and keep fixture imports stable** - `e99c162` (test)
3. **Task 3: Remove root-level backend leftovers and prove parity at api scope** - `33adb15` (chore)

## Files Created/Modified
- `api/app/main.py` - FastAPI app bootstrap and router wiring under api/.
- `api/requirements.txt` - Backend dependencies owned by api/.
- `api/environment.yml` - Backend runtime environment owned by api/.
- `api/pytest.ini` - api-local pytest configuration.
- `api/tests/conftest.py` - TestClient fixture for api-local suite.
- `api/tests/features/prediction/test_router.py` - Adjusted test setup to avoid rate-limit leakage.

## Decisions Made
- Keep python package name as `app.*` so running from api/ continues to use `uvicorn app.main:app`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Prevented rate-limit state leakage between prediction router tests**
- **Found during:** Task 2 (Relocate backend tests into api/ and keep fixture imports stable)
- **Issue:** Moving tests exposed a 429 response from reused rate-limit state in `test_predict_endpoint_probability_range`.
- **Fix:** Injected a high-capacity rate limiter for that test to keep expected 200 responses.
- **Files modified:** `api/tests/features/prediction/test_router.py`
- **Verification:** `cd api; pytest -q`
- **Committed in:** `e99c162` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Required to keep existing tests deterministic; no change to API contract.

## Issues Encountered
- Rate-limit state persisted across tests causing a single 429; resolved by isolating rate-limit settings for the affected test.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend boundary is isolated under api/ with tests passing locally.
- Ready to introduce api-local env contracts and workflow scripts in the next phase.

---
*Phase: 01-app-boundary-migration-backend-parity*
*Completed: 2026-04-11*

## Self-Check: PASSED
- FOUND: .planning/phases/01-app-boundary-migration-backend-parity/01-01-SUMMARY.md
- FOUND: 430d20f
- FOUND: e99c162
- FOUND: 33adb15
