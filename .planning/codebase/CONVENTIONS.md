# Coding Conventions

**Analysis Date:** 2026-04-12

## Naming Patterns

**Files:**
- Use `snake_case.py` for modules in app and tests (examples: `api/app/features/prediction/service.py`, `api/app/middleware/rate_limit/service.py`, `api/tests/features/prediction/test_service.py`).
- Use `test_*.py` for test files (examples: `api/tests/core/test_ohlcv.py`, `api/tests/middleware/rate_limit/test_bucket.py`).
- Use package markers `__init__.py` in each directory (examples: `api/app/features/prediction/__init__.py`, `api/tests/features/historic_data/__init__.py`).

**Functions:**
- Use `snake_case` function and method names (examples: `get_prediction_service()` in `api/app/features/prediction/router.py`, `fetch_hourly_ohlcv()` in `api/app/features/historic_data/service.py`, `_resolve_client_ip()` in `api/app/middleware/rate_limit/service.py`).
- Use `get_*` naming for FastAPI dependency factories (examples: `get_service()` in `api/app/features/historic_data/router.py`, `get_prediction_service()` in `api/app/features/prediction/router.py`).
- Prefix private helpers with `_` (examples: `_extract_probabilities()` in `api/app/features/prediction/service.py`, `_normalize_path()` in `api/app/middleware/rate_limit/service.py`, `_seconds_until_next_token()` in `api/app/middleware/rate_limit/bucket.py`).

**Variables:**
- Use `snake_case` for variables and attributes (examples: `mock_kraken_payload` in `api/tests/features/prediction/test_service.py`, `latest_features` in `api/app/features/prediction/service.py`, `retry_after_seconds` in `api/app/middleware/rate_limit/schemas.py`).
- Use descriptive names for booleans (`is_exempt`, `is_new`) in `api/app/middleware/rate_limit/service.py` and `api/app/middleware/rate_limit/storage.py`.

**Types:**
- Use PascalCase for classes and Pydantic models (`PredictionService`, `ModelLoader`, `RateLimitPolicy`, `PredictionRequest`).
- Use built-in generics and modern unions (`dict[str, int | str]`, `RateLimitState | None`) in `api/app/shared/ohlcv/kraken_api.py` and `api/app/middleware/rate_limit/storage.py`.
- Prefer constants in `UPPER_SNAKE_CASE` when values are shared (`REQUIRED_COLUMNS`, `COLUMNS_TO_DROP` in `api/app/features/prediction/service.py`).

## Code Style

**Formatting:**
- Keep line breaks and argument wrapping Black-compatible style, as shown in `api/app/main.py` and `api/app/features/prediction/service.py`.
- Tool used: Not detected (no `pyproject.toml`, `.flake8`, `setup.cfg`, or `tox.ini` at repository root).

**Linting:**
- Use triple double-quoted docstrings for modules/classes/functions throughout `api/app/` and `api/tests/`.
- Tool used: Not detected (no lint config found at repository root).

**Type Annotations:**
- Enforce typed APIs by convention with explicit annotations in service and middleware code (`api/app/features/historic_data/service.py`, `api/app/middleware/rate_limit/bucket.py`).
- Keep `# type: ignore` only at framework-signature edges (`api/app/middleware/rate_limit/middleware.py`).

## Import Organization

**Order:**
- Use absolute package paths rooted at `app` (example: `from app.shared.ohlcv import KrakenAPIClient` in `api/app/features/historic_data/service.py`).
- Not used: Path aliases or explicit group sorting.

**Path Aliases:**
- Not used: No path alias configuration detected.

## Error Handling

**Patterns:**
- Raise domain exceptions from service/adapter layers using `api/app/core/exceptions.py` (`DataFetchError`, `DataValidationError`, `InsufficientDataError`, `ModelNotLoadedError`).
- Map domain exceptions to HTTP responses in global handlers in `api/app/main.py`.
- Preserve root cause with exception chaining (`raise ... from error`) in `api/app/shared/ohlcv/kraken_api.py`, `api/app/shared/ohlcv/ohlc_dataframe.py`, and `api/app/features/prediction/service.py`.
- Validate external payload shape early and fail fast (`KrakenAPIClient._validate_api_response()` in `api/app/shared/ohlcv/kraken_api.py`; `OHLCVDataFrame.from_kraken_response()` in `api/app/shared/ohlcv/ohlc_dataframe.py`).

## Logging

**Framework:** `logging` module (standard library)

**Patterns:**
- Configure global format/level in `api/app/main.py` with `logging.basicConfig(...)` using settings from `api/app/core/config.py`.
- Use module loggers (`logger = logging.getLogger(__name__)`) in service modules like `api/app/features/prediction/service.py` and `api/app/features/historic_data/service.py`.
- Log lifecycle milestones and counts (rows/features) instead of raw payloads (`PredictionService` logs in `api/app/features/prediction/service.py`).
- Use `warning` for validation-like failures and `error` for upstream/model failures in global handlers (`api/app/main.py`).

## Comments

**When to Comment:**
- Use module-level docstrings to explain purpose and rationale (examples: `api/app/main.py`, `api/app/shared/ohlcv/ohlc_dataframe.py`, `api/tests/features/historic_data/test_service.py`).
- Add brief "why" comments around non-obvious logic (examples: singleton lock comment in `api/app/features/prediction/service.py`, incomplete-candle drop in `api/app/shared/ohlcv/ohlc_dataframe.py`).
- Do not add line-by-line comments for obvious operations.

**JSDoc/TSDoc:**
- Not applicable (Python codebase).

**Docstrings:**
- Use Python docstrings consistently for API contracts and test intent across `api/app/` and `api/tests/`.

## Function Design

**Size:**
- Keep public orchestration methods thin and delegate steps to private helpers (pattern in `PredictionService.predict()` in `api/app/features/prediction/service.py`).

**Parameters:**
- Inject dependencies through constructor parameters with `None` defaults and internal fallback instantiation (`PredictionService.__init__()` in `api/app/features/prediction/service.py`, `HistoricDataService.__init__()` in `api/app/features/historic_data/service.py`).
- Keep endpoint functions typed and DI-driven (`predict_price_movement()` in `api/app/features/prediction/router.py`, `get_live_data()` in `api/app/features/historic_data/router.py`).

**Return Values:**
- Return Pydantic response models from service boundaries (`PredictionResponse` in `api/app/features/prediction/service.py`, `HistoricDataResponse` in `api/app/features/historic_data/service.py`).
- Use tuple returns only for tightly-coupled internal outputs (`TokenBucket.consume()` in `api/app/middleware/rate_limit/bucket.py`).

## Module Design

**Exports:**
- Keep imports explicit from concrete modules (for example, `from app.features.prediction.service import PredictionService` in `api/app/features/prediction/router.py`).
- Use selective package exports where shared contracts are needed (`api/app/shared/ohlcv/__init__.py`, `api/app/middleware/rate_limit/__init__.py`).

**Barrel Files:**
- Use minimal barrel files only for shared primitives (`api/app/shared/ohlcv/__init__.py`, `api/app/middleware/rate_limit/__init__.py`).
- Keep feature package `__init__.py` empty when no stable re-export contract is required (`api/app/features/prediction/__init__.py`, `api/app/features/historic_data/__init__.py`).

---

*Convention analysis: 2026-04-12*