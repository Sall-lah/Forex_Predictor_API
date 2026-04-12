# Testing Patterns

**Analysis Date:** 2026-04-12

## Test Framework

**Runner:**
- pytest (version unpinned)
- Config: `api/pytest.ini`
- Markers defined: `integration`, `ratelimit_perf`, `ratelimit_soak`

**Assertion Library:**
- pytest built-in assertions (`pytest.raises`, `pytest.approx`, `assert ... is ...`)

**Run Commands:**
```bash
pytest                          # Run all tests
pytest -m integration          # Run integration tests only
pytest tests/features/prediction/ # Run prediction feature tests
```

## Test File Organization

**Location:**
- Co-located with feature code under `api/tests/features/<feature>/` and `api/tests/middleware/<middleware>/`.
- Shared fixtures in `api/tests/conftest.py`.

**Naming:**
- `test_*.py` for test files (examples: `test_service.py`, `test_router.py`, `test_integration.py`, `test_bucket.py`).

**Structure:**
```
api/tests/
├── conftest.py              # Shared fixtures (TestClient)
├── core/
│   └── test_ohlcv.py     # OHLCV validation tests
├── features/
│   ├── prediction/
│   │   ├── test_service.py
│   │   ├── test_router.py
│   │   ├── test_integration.py
│   │   └── __init__.py
│   └── historic_data/
│       ├── test_service.py
│       ├── test_router.py
│       ├── test_integration.py
│       └── __init__.py
└── middleware/
    └── rate_limit/
        ├── test_middleware.py
        ├── test_service.py
        ├── test_bucket.py
        ├── test_storage.py
        ├── test_performance.py
        └── __init__.py
```

## Test Structure

**Suite Organization:**
```python
"""
Tests for the <Feature>Service class.

Why mock X: <Reason for mocking approach>.
"""

import pytest
from unittest.mock import Mock

from app.features.<feature>.service import <Feature>Service
from app.core.exceptions import DomainException


def test_service_method_success(mocker):
    """Test successful workflow with all dependencies mocked."""
    service = <Feature>Service()
    
    # Mock external dependencies
    mocker.patch.object(service.api_client, "method", return_value=expected)
    
    # Execute
    result = service.method(request)
    
    # Assert
    assert result.expected_attr == expected_value
    service.api_client.method.assert_called_once()


def test_service_handles_domain_error(mocker):
    """Domain exceptions should propagate correctly."""
    mocker.patch.object(
        service.api_client, 
        "method", 
        side_effect=DomainException("error message")
    )
    
    with pytest.raises(DomainException, match="error message"):
        service.method(request)
```

**Patterns:**
- Use docstrings to explain test intent and mocking rationale
- Structure as: Setup → Mock dependencies → Execute → Assert → Verify mocks
- Use `mocker.patch.object()` for method-level mocking
- Use `monkeypatch` for configuration patching

## Mocking

**Framework:** pytest-mock (`mocker` fixture)

**Patterns:**
```python
# Mock a method on an injected dependency
mocker.patch.object(service.api_client, "fetch_ohlcv_data", return_value=mock_payload)

# Mock a class method
mocker.patch.object(ClassName, "class_method", return_value=mock_value)

# Mock module-level function
mocker.patch("module.path.function_name", return_value=mock_value)

# Mock with side effect for exceptions
mocker.patch.object(
    service.api_client, 
    "method", 
    side_effect=DomainException("error context")
)
```

**What to Mock:**
- HTTP clients (`httpx.get`) in service tests
- External API responses (Kraken JSON payloads)
- Model loading (`joblib.load`)
- Time-dependent logic (`monotonic` or custom clock)

**What NOT to Mock:**
- Business logic being tested (validate input, extract features)
- Pydantic validation (use real schemas)
- In-memory storage state (test directly if possible)

## Fixtures and Factories

**Test Data:**
```python
# Generate test OHLCV data programmatically
dummy_data = []
for i in range(168):  # 1 week of hourly data
    o = 60000.0 + (i % 10) * 10
    h = o + 500.0
    l = o - 500.0
    c = o + 100.0
    dummy_data.append([
        base_time + i * 3600,  # timestamp
        str(o), str(h), str(l), str(c),  # OHLC
        "60000.0", "1.5", 10  # vwap, volume, count
    ])

mock_payload = {
    "error": [],
    "result": {pair: dummy_data, "last": base_time + 167 * 3600},
}
```

**Location:**
- Inline in test functions for specific test cases
- Create helper functions at module level for reusable test data

## Coverage

**Requirements:** None enforced

**View Coverage:**
```bash
pytest --cov=app --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Test individual service methods with mocked dependencies
- Test error handling paths (domain exceptions propagate correctly)
- Test feature extraction (OHLCVPreprocessor.validate_input)
- Test token bucket math (TokenBucket.consume)

**Integration Tests:**
- Marked with `@pytest.mark.integration`
- Test full HTTP flow with TestClient
- Include rate-limit middleware behavior
- May hit real external APIs (Kraken) in optional `ratelimit_soak` tests

**E2E Tests:**
- Not used. Use TestClient-based integration tests instead.

## Common Patterns

**Async Testing:**
```python
# Service methods are synchronous - use pytest directly
response = service.method(request)
assert response.expected_attr == expected_value
```

**Error Testing:**
```python
# Test domain exception propagation
with pytest.raises(DomainException) as exc_info:
    service.method(invalid_request)

assert "expected message" in str(exc_info.value)
```

**Fixture Injection:**
```python
# FastAPI TestClient fixture in conftest.py
@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)
```

**Mocked Client Injection:**
```python
# Inject mocked dependencies through constructor
mock_client = Mock()
mock_client.method.return_value = mock_payload
service = <Feature>Service(api_client=mock_client)
```

**Configuration Patching:**
```python
# Use monkeypatch for settings overrides
monkeypatch.setattr(settings, "MODEL_DIR", str(tmp_path))
monkeypatch.setattr(settings, "MODEL_FILENAME", "test-model.pkl")
```

---

*Testing analysis: 2026-04-12*