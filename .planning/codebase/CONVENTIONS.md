# Coding Conventions

**Analysis Date:** 2026-04-12

## Naming Patterns

**Files:**
- Backend (Python): `snake_case.py` for modules (e.g., `api/app/features/prediction/service.py`) and `test_*.py` for test files. Package markers `__init__.py` in each directory.
- Frontend (TypeScript/React): Typically `PascalCase.tsx` for components and `camelCase.ts` or `kebab-case.ts` for utilities (inferred from React Vite defaults).

**Functions:**
- `snake_case` in Python (e.g., `get_prediction_service()`).
- `get_*` prefix for FastAPI dependency factories.
- Private helpers use `_` prefix (e.g., `_extract_probabilities()`).

**Variables:**
- `snake_case` in Python (e.g., `latest_features`, `retry_after_seconds`).
- Descriptive names for booleans (e.g., `is_exempt`, `is_new`).
- Constants use `UPPER_SNAKE_CASE` when shared (e.g., `REQUIRED_COLUMNS`).

**Types:**
- PascalCase for classes and Pydantic models (e.g., `PredictionService`, `PredictionRequest`).

## Code Style

**Formatting:**
- Black-compatible style in Python, breaking arguments cleanly.
- No explicit tool config (e.g., `pyproject.toml`, `.prettierrc`) at the repository root.

**Linting:**
- No root `.flake8` or `eslint.config.js` detected. Enforce typed APIs by convention with explicit annotations.
- Keep `# type: ignore` only at framework-signature edges (e.g., `api/app/middleware/rate_limit/middleware.py`).

## Import Organization

**Order:**
- Absolute package paths rooted at `app` for internal imports (e.g., `from app.shared.ohlcv import KrakenAPIClient`).

**Path Aliases:**
- Not used; no explicit path alias configuration detected for Python.

## Error Handling

**Patterns:**
- Raise domain exceptions from service/adapter layers using `api/app/core/exceptions.py` (e.g., `DataFetchError`, `InsufficientDataError`).
- Map domain exceptions to HTTP responses in global handlers in `api/app/main.py`.
- Preserve root cause with exception chaining (`raise ... from error`).
- Validate external payload shapes early and fail fast (`KrakenAPIClient._validate_api_response()`).

## Logging

**Framework:** `logging` module (Python)

**Patterns:**
- Configure global format/level in `api/app/main.py` using `logging.basicConfig(...)` with settings from `api/app/core/config.py`.
- Module loggers instantiated via `logger = logging.getLogger(__name__)`.
- Log lifecycle milestones and aggregated metrics (counts, shapes), NOT raw payloads.
- Use `warning` for validation failures, `error` for upstream/model crashes.

## Comments

**When to Comment:**
- Use module-level docstrings to explain purpose and rationale.
- Add brief "why" comments around non-obvious logic (e.g., singleton lock comments, incomplete-candle drops).
- Avoid line-by-line comments for obvious operations.

**JSDoc/TSDoc / Python Docstrings:**
- Use triple double-quoted docstrings `"""` for modules/classes/functions across `api/app/` and `api/tests/`.
- Document test intent in docstrings.

## Function Design

**Size:** Thin public orchestration methods; delegate complex steps to private helpers (`PredictionService.predict()`).

**Parameters:** Inject dependencies through constructor parameters with `None` defaults or FastAPI `Depends()`.

**Return Values:** Return Pydantic response models from service boundaries (`PredictionResponse`, `HistoricDataResponse`). Tuple returns only for tightly-coupled internal outputs.

## Module Design

**Exports:** 
- Keep imports explicit from concrete modules (e.g., `from app.features.prediction.service import PredictionService`).

**Barrel Files:**
- Use minimal barrel files (`__init__.py`) only for shared primitives (e.g., `api/app/shared/ohlcv/__init__.py`). Keep feature packages empty when no stable re-export contract is required.
