# AGENTS.md - Developer Guide for AI Coding Agents

This guide provides essential information for AI coding agents working in the Forex Predictor API repository.

## Project Overview

A FastAPI-based REST API for forex/crypto predictions using LSTM models with technical indicator enrichment.

**Tech Stack:** Python 3.12, FastAPI, joblib, pandas 2.2.2, numpy 2.0.2, scikit-learn 1.6.1, ta (technical analysis)

## Build & Test Commands

### Environment Setup
```bash
# Create conda environment
conda env create -f environment.yml
conda activate forex_prediction

# Or use pip
pip install -r requirements.txt
```

### Running the Application
```bash
# Development server with auto-reload
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing Commands
```bash
# Run all tests
pytest

# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run a single test file
pytest tests/features/historic_data/test_service.py

# Run a single test function
pytest tests/features/historic_data/test_service.py::test_fetch_hourly_ohlcv_success

# Run tests matching a pattern
pytest -k "test_fetch"

# Run with verbose output
pytest -v

# Run tests in a specific directory
pytest tests/features/historic_data/
```

### Linting & Code Quality
```bash
# No explicit linters configured yet
# Consider adding: ruff, black, mypy, isort
```

## Code Style Guidelines

### Import Organization
```python
# Standard library imports first
import logging
from typing import List, Optional
from datetime import datetime

# Third-party imports second
import httpx
import pandas as pd
import ta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

# Local application imports last
from app.core.config import get_settings
from app.core.exceptions import DataFetchError, DataValidationError
from app.features.historic_data.schemas import HistoricDataRequest
```

### Type Hints
- **REQUIRED** for all function signatures (args + return type)
- Use modern syntax: `dict[str, str]` not `Dict[str, str]`
- Use `Optional[T]` for nullable types
- Example:
```python
def get_settings() -> Settings:
    return Settings()

async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
```

### Naming Conventions
- **Modules/Files:** `snake_case.py` (e.g., `historic_data/service.py`)
- **Classes:** `PascalCase` (e.g., `HistoricDataService`, `BaseAppException`)
- **Functions/Methods:** `snake_case` (e.g., `compute_indicators`, `fetch_hourly_ohlcv`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `_KRAKEN_OHLC_URL`, `_DEFAULT_SMA_PERIOD`)
- **Private methods:** Prefix with `_` (e.g., `_validate_dataframe`, `_enrich_dataframe`)
- **Pydantic models:** Descriptive names ending in schema type (e.g., `HistoricDataRequest`, `EnrichedOHLCVRecord`)

### Docstrings
- **Module-level:** Explain purpose and architectural rationale
- **Class-level:** Describe responsibility and design decisions
- **Public methods:** Full docstring with Args, Returns, Raises sections
- **Private methods:** Brief one-liner explaining purpose
- Use Google-style or NumPy-style format
- Example:
```python
def compute_indicators(self, request: HistoricDataRequest) -> HistoricDataResponse:
    """
    Accept validated OHLCV data, compute indicators (SMA, RSI, MACD, MACD_signal),
    and return an enriched response.

    Args:
        request: Validated HistoricDataRequest containing raw candles
                 and desired indicator periods.

    Returns:
        HistoricDataResponse with original OHLCV data plus indicator columns.

    Raises:
        InsufficientDataError: When the number of candles is less than
                               the requested indicator window.
        DataValidationError: When the data contains structural issues
                             that prevent computation.
    """
```

### Error Handling
- Use **custom domain exceptions** from `app.core.exceptions`
- Never let raw exceptions bubble to the client
- Exception hierarchy:
  - `BaseAppException` → base for all app errors (500)
  - `ModelNotLoadedError` → ML model unavailable (503)
  - `DataFetchError` → upstream data source failure (502)
  - `DataValidationError` → domain validation failure (422)
  - `InsufficientDataError` → not enough data rows (422)
- Raise with descriptive messages:
```python
raise DataFetchError(f"Network error while fetching Kraken data for '{pair}': {exc}") from exc
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

# Use appropriate levels
logger.info("Fetched and enriched Kraken data for '%s' — %d hourly candles.", pair, len(records))
logger.warning("DataValidationError: %s", exc.message)
logger.error("ModelNotLoadedError: %s", exc.message)
```

### FastAPI Patterns
- **Routers:** Thin controllers in `app/features/{feature}/router.py`
- **Services:** Business logic in `app/features/{feature}/service.py`
- **Schemas:** Pydantic models in `app/features/{feature}/schemas.py`
- **Dependency injection:** Use `Depends()` for testability
```python
def get_historic_data_service() -> HistoricDataService:
    return HistoricDataService()

@router.post("/compute-indicators")
async def compute_indicators(
    request: HistoricDataRequest,
    service: HistoricDataService = Depends(get_historic_data_service),
) -> HistoricDataResponse:
    return service.compute_indicators(request)
```

### Testing Standards
- Place tests in `tests/` mirroring `app/` structure
- Use `pytest` fixtures defined in `tests/conftest.py`
- Mock external API calls using `pytest-mock` (mocker fixture)
- Fixture scopes: `module` for TestClient to avoid overhead
- Test naming: `test_{method_name}_{scenario}` (e.g., `test_fetch_hourly_ohlcv_success`)
- Example:
```python
def test_fetch_hourly_ohlcv_success(mocker):
    service = HistoricDataService()
    mock_response = Mock()
    mock_response.json.return_value = {"error": [], "result": {...}}
    mocker.patch("httpx.get", return_value=mock_response)
    
    response = service.fetch_hourly_ohlcv("XXBTZUSD")
    assert response.total_records > 0
```

## Project Structure

```
app/
├── api/           # API router aggregation
├── core/          # Config, exceptions, shared utilities
├── features/      # Feature modules (historic_data, prediction)
│   └── {feature}/
│       ├── router.py   # FastAPI routes
│       ├── schemas.py  # Pydantic models
│       └── service.py  # Business logic
└── main.py        # FastAPI app + global exception handlers

tests/
└── features/      # Tests mirror app structure
    └── {feature}/
        ├── test_router.py
        ├── test_service.py
        └── test_integration.py
```

## Key Architectural Principles

1. **Separation of concerns:** Routers ≠ Services. Keep HTTP handling separate from business logic.
2. **Domain exceptions:** Services raise framework-agnostic exceptions; global handlers convert to HTTP.
3. **Dependency injection:** Use FastAPI's `Depends()` for testability.
4. **Type safety:** Use Pydantic for validation and type-safe configs.
5. **Pandas operations:** Use vectorized operations only—never `iterrows()`.
6. **Environment config:** Load from `.env` via `pydantic-settings`, never hardcode.

## Rate Limiter Architecture

Runtime flow is intentionally layered: `app.main` → `RateLimitMiddleware.dispatch()` → `RateLimiterService.evaluate()` → `TokenBucket.consume()` + `InMemoryRateLimitStorage`.

- **`app.main` (`app/main.py`)**
  - Registers `RateLimitMiddleware` once for all requests (`app.add_middleware(RateLimitMiddleware)`).
  - Keeps startup wiring concerns separate from rate-limit decision logic.
- **`RateLimitMiddleware.dispatch()` (`app/middleware/rate_limit/middleware.py`)**
  - Thin HTTP boundary layer.
  - Resolves a `RateLimiterService` instance, calls `evaluate()`, and translates the service decision into headers / `429` JSON response.
  - **Do not move business logic into middleware.** Keep policy and identity rules in the service layer.
- **`RateLimiterService.evaluate()` (`app/middleware/rate_limit/service.py`)**
  - Core orchestration layer for rate-limit behavior.
  - Applies exempt-path rules, resolves effective client IP (trusted-proxy aware), maps path to endpoint policy, and coordinates bucket + storage state updates.
- **`TokenBucket.consume()` (`app/middleware/rate_limit/bucket.py`)**
  - Stateless token math (allow/deny decision, remaining tokens, reset/retry timing).
  - Must stay deterministic and independent from HTTP concerns.
- **`InMemoryRateLimitStorage` (`app/middleware/rate_limit/storage.py`)**
  - Async-safe bucket state persistence keyed by client/policy.
  - Enforces capacity guardrails and TTL cleanup to prevent unbounded memory growth.

## Rate Limiter Extension Checklist

When adding/changing rate-limiting behavior, use this checklist to preserve architecture boundaries and avoid regressions:

1. **Add configuration fields in `Settings` first** (`app/core/config.py`)
   - Define new `RATE_LIMIT_*` values with safe defaults.
   - Keep naming aligned with existing environment variable style.
2. **Map route prefix to policy in `RateLimiterService._resolve_policy()`**
   - Add/adjust path-prefix mapping and select the matching `RateLimitPolicy` values.
   - Keep matching logic centralized in service (not middleware/router).
3. **Update middleware and service tests**
   - Add or adjust tests in `tests/middleware/rate_limit/test_middleware.py` for policy selection, headers, and deny behavior.
4. **Run targeted verification before merge**
   - `pytest tests/middleware/rate_limit/ -x`
5. **If changing exemptions or spoofing rules**
   - Update `docs/rate-limiter-configuration.md` (`Exempt Endpoints and Security Notes`).
   - Add regression tests that cover proxy spoofing and exemption bypass edge cases.

For exemption behavior details and anti-bypass rules, always consult `docs/rate-limiter-configuration.md` (`Exempt Endpoints and Security Notes`) before modifying `RateLimiterService` path/proxy logic.

## Common Pitfalls to Avoid

- ❌ Don't use `iterrows()` or row-by-row operations—use pandas vectorization
- ❌ Don't hardcode config values—use `app.core.config.Settings`
- ❌ Don't catch raw `Exception`—use specific domain exceptions
- ❌ Don't put business logic in routers—delegate to services
- ❌ Don't skip type hints on function signatures
- ❌ Don't forget to handle NaN values when converting DataFrames to Pydantic models (use `.where(pd.notnull(df), None)`)

## Known Issues

- Missing implementation: `_validate_dataframe()` and `_records_to_dataframe()` methods are called but not defined in `HistoricDataService`
