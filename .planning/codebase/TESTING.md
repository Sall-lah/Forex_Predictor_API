# Testing Patterns

**Analysis Date:** 2026-04-12

## Test Framework

**Runner:**
- `pytest` (Python Backend)
- Framework configured via `api/pytest.ini` with custom markers (e.g., `integration`, `ratelimit_perf`, `ratelimit_soak`).

**Assertion Library:**
- Native `assert` from `pytest`.

**Run Commands:**
```bash
pytest                 # Run all tests
pytest -m integration  # Run marked integration tests
```

## Test File Organization

**Location:**
- Separate folder matching module structure (`api/tests/features/historic_data/`, `api/tests/features/prediction/`).

**Naming:**
- Prefix with `test_` (e.g., `test_service.py`, `test_router.py`, `test_ohlcv.py`).

**Structure:**
```
api/tests/
├── conftest.py           # Shared fixtures
├── core/                 # Shared unit tests
└── features/
    └── [feature_name]/
        ├── test_service.py
        └── test_router.py
```

## Test Structure

**Suite Organization:**
```python
"""
Unit tests for PredictionService with mocked dependencies.

Tests:
- Successful prediction flow
- Kraken API fetch errors
- Insufficient data errors
"""
```

**Patterns:**
- Use FastAPI `TestClient` instantiated with `scope="module"` in `api/tests/conftest.py` to test routers and HTTP boundaries.
- Mock external APIs (Kraken API) directly at the HTTP client or service boundary.
- Test both sunny-day (success flow) and rainy-day (fetch errors, bad models) paths explicitly.

## Mocking

**Framework:** `unittest.mock` (Mock, MagicMock)

**Patterns:**
```python
from unittest.mock import Mock, MagicMock
mock_service = Mock()
mock_service.predict = MagicMock(return_value={"probability": 0.85})
```

**What to Mock:**
- External network interactions (Kraken API).
- File system loads (ModelLoader parsing `.pkl` artifacts).

**What NOT to Mock:**
- Pydantic validation (test schemas directly to ensure proper data modeling).
- Internal domain exceptions mapping.

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)
```

**Location:**
- Shared API-wide fixtures (like `client`) reside in `api/tests/conftest.py`.
- Module-specific mock data (e.g., `mock_kraken_payload`) is declared in the target `test_*.py` file.

## Coverage

**Requirements:** Checked via `pytest-cov`, no strict percentage enforced globally.

**View Coverage:**
```bash
pytest --cov=app --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Validate discrete service methods, domain exception raising, and data frame manipulation (`api/tests/core/test_ohlcv.py`).

**Integration Tests:**
- Exercise the complete API request flow using `TestClient` (e.g., `api/tests/features/prediction/test_integration.py`).

**E2E Tests:**
- Not strictly implemented; integration tests cover HTTP-to-Mocked-Kraken.

## Common Patterns

**Async Testing:**
```python
import pytest
@pytest.mark.asyncio
async def test_async_service_method():
    # test logic
    pass
```

**Error Testing:**
```python
import pytest
from app.core.exceptions import DataFetchError

def test_fetch_failure():
    with pytest.raises(DataFetchError) as exc_info:
        # call triggering failure
        pass
    assert "Expected message" in str(exc_info.value)
```
