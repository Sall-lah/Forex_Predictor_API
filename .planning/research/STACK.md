# Technology Stack - Rate Limiting

**Project:** Token Bucket Rate Limiter for Forex Predictor API
**Researched:** 2026-03-31
**Focus:** Greenfield rate limiting implementation for FastAPI

## Executive Summary

For a greenfield token bucket rate limiter in FastAPI, the **recommended approach is custom implementation** using Python's standard library. No external rate limiting library is necessary because:
1. Project requires in-memory storage only (single instance deployment)
2. Token bucket algorithm is straightforward to implement
3. Full control over logic matches project's "production-ready with clean architecture" goal
4. No external dependencies = simpler deployment and testing

**Confidence:** HIGH - Based on official PyPI package data (Feb 2026), project requirements analysis, and FastAPI architectural patterns.

## Recommended Stack

### Core Implementation (Custom Code)

| Component | Technology | Version | Why |
|-----------|-----------|---------|-----|
| **Storage** | Python `dict` + `collections.deque` | Standard library | Thread-safe with proper locking; zero dependencies; fast O(1) lookups |
| **Time Source** | `time.time()` or `time.monotonic()` | Standard library | `monotonic()` prevents clock adjustments from breaking rate limits |
| **Concurrency** | `threading.RLock` | Standard library | Allows re-entrant locking for nested calls; Python 3.12 compatible |
| **Middleware** | FastAPI `BaseHTTPMiddleware` | FastAPI built-in | Native integration with request/response cycle |
| **Configuration** | `pydantic-settings` | Already in stack | Consistent with existing `app/core/config.py` patterns |
| **Type Safety** | `typing` + Pydantic models | Standard library + existing | Full type hints for configuration and internal state |

### Supporting Libraries (Already Available)

| Library | Current Version | Purpose | Notes |
|---------|----------------|---------|-------|
| FastAPI | latest | Web framework | Already in `environment.yml` |
| pydantic | latest | Data validation | Already in `environment.yml` |
| pydantic-settings | latest | Config management | Already in `environment.yml` |

## Alternatives Considered (NOT Recommended)

### Option 1: slowapi (Popular Library)
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Approach | **Custom implementation** | slowapi 0.1.9 | Last release Feb 2024; Flask-limiter port; requires `limits` library; fixed-window focused; decorator-heavy API doesn't fit middleware pattern |

**slowapi Analysis:**
- **Pros:** Battle-tested (1.9k stars), production usage, decorator support
- **Cons:** 
  - Dependency on `limits` library (adds complexity)
  - Primarily fixed-window algorithm (project needs token bucket)
  - Decorator pattern conflicts with middleware-first architecture
  - Requires passing `request` to every endpoint explicitly
  - Not updated since Feb 2024
- **Confidence:** HIGH (official PyPI data)

### Option 2: fastapi-limiter (Newer Alternative)
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Approach | **Custom implementation** | fastapi-limiter 0.2.0 | Released Feb 2026; depends on `pyrate-limiter`; designed for Redis/external storage; overkill for in-memory needs |

**fastapi-limiter Analysis:**
- **Pros:** Very recent (Feb 2026), clean async support, supports Python 3.12
- **Cons:**
  - Requires `pyrate-limiter` (complex leaky bucket library)
  - Designed for distributed systems (Redis/Postgres)
  - Over-engineered for single-instance in-memory use case
  - Adds 2 external dependencies vs 0 for custom implementation
- **Confidence:** HIGH (official PyPI data)

### Option 3: pyrate-limiter (Underlying Engine)
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Approach | **Custom implementation** | pyrate-limiter 4.1.0 | Released Mar 2026; feature-rich but complex; supports Redis, Postgres, SQLite; designed for multi-backend scenarios |

**pyrate-limiter Analysis:**
- **Pros:** 
  - Latest release Mar 2026 (very current)
  - Supports Python 3.10-3.14
  - Leaky bucket algorithm (similar to token bucket)
  - Multiple backend support
- **Cons:**
  - Designed for complex use cases (multiprocess, Redis, Postgres)
  - Requires BucketFactory abstraction (overkill)
  - InMemoryBucket is simplest mode but still wraps basic data structures
  - Library abstraction makes debugging harder than custom code
  - Single-instance use case doesn't justify library complexity
- **Confidence:** HIGH (official PyPI and GitHub data)

### Option 4: limits (Core Algorithm Library)
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Approach | **Custom implementation** | limits 5.8.0 | Released Feb 2026; low-level rate limiting library; used by slowapi; provides fixed window, moving window, sliding window |

**limits Analysis:**
- **Pros:**
  - Very recent (Feb 2026)
  - Production-stable (5.x release)
  - Supports async/sync
  - Multiple algorithms available
- **Cons:**
  - Requires Python >=3.10 (project uses 3.12, compatible but restrictive)
  - Provides fixed/moving/sliding window, NOT pure token bucket
  - Storage backends (Redis, Memcached, MongoDB) unnecessary for in-memory
  - Adds dependency when stdlib + custom code suffices
  - Algorithm mismatch (project specifies token bucket)
- **Confidence:** HIGH (official PyPI data)

## Custom Implementation Components

### 1. Token Bucket Class
```python
# app/middleware/rate_limit/bucket.py
from collections import deque
from dataclasses import dataclass
import time
from typing import Optional

@dataclass
class TokenBucket:
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float
    last_refill: float
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.monotonic()
```

**Why:** 
- Token bucket algorithm as specified in requirements
- `monotonic()` prevents system clock adjustments from breaking limits
- Simple dataclass = easy testing and debugging
- No external dependencies

### 2. In-Memory Storage
```python
# app/middleware/rate_limit/storage.py
from threading import RLock
from typing import Dict

class InMemoryStorage:
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = RLock()
```

**Why:**
- `RLock` allows re-entrant locking (safe for nested calls)
- Plain dict = O(1) lookups, simple to reason about
- Thread-safe with explicit lock = predictable concurrency
- No Redis/external dependencies = simpler deployment

### 3. FastAPI Middleware
```python
# app/middleware/rate_limit/middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Token bucket logic here
        ...
```

**Why:**
- `BaseHTTPMiddleware` is FastAPI's standard middleware pattern
- Automatic application to all routes
- Access to request/response cycle
- Consistent with existing FastAPI architecture

### 4. Configuration
```python
# app/core/config.py (extend existing Settings class)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Existing settings...
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 500
    RATE_LIMIT_BURST: int = 10
    RATE_LIMIT_EXEMPT_ENDPOINTS: list[str] = ["/health", "/docs", "/openapi.json", "/redoc"]
```

**Why:**
- Uses existing `pydantic-settings` pattern
- Environment-variable configuration
- Type-safe with validation
- Consistent with current `app/core/config.py`

## Installation

No additional dependencies required. All components use Python standard library or existing stack.

```bash
# No new packages needed!
# Existing environment.yml already has:
# - FastAPI
# - pydantic
# - pydantic-settings
```

## Anti-Patterns to Avoid

### ❌ Don't: Use Redis for single-instance deployment
**Why:** Redis adds operational complexity (deployment, monitoring, connection management) with zero benefit for single-instance in-memory storage.

### ❌ Don't: Add slowapi/fastapi-limiter libraries
**Why:** 
- External dependency for functionality implementable in ~200 lines
- Libraries designed for different use cases (fixed window, distributed systems)
- Harder to customize/debug than owned code
- Testing requires mocking library internals

### ❌ Don't: Use `time.time()` without considering monotonic alternatives
**Why:** System clock adjustments (NTP sync, DST) can cause token bucket to behave incorrectly. `time.monotonic()` is immune to clock changes.

### ❌ Don't: Implement with global mutable state without locks
**Why:** FastAPI is async and multi-threaded. Race conditions will corrupt bucket state without proper locking.

### ❌ Don't: Skip per-endpoint configuration
**Why:** Expensive endpoints (ML predictions) need stricter limits than health checks. Generic rate limiting causes UX issues.

## Migration Path (If Scaling Later)

If future requirements change (multi-instance deployment, Redis needed):

1. **Keep abstractions:** Storage interface allows swapping implementations
2. **Add Redis backend:** Implement `RedisStorage` class with same interface
3. **Use pyrate-limiter:** At that point, library complexity is justified
4. **Configuration toggle:** `RATE_LIMIT_STORAGE_TYPE=redis` vs `memory`

**Current recommendation:** Don't prematurely optimize. Custom implementation serves current needs perfectly.

## Sources

### HIGH Confidence
- PyPI slowapi: https://pypi.org/project/slowapi/ (Feb 2024 release)
- PyPI fastapi-limiter: https://pypi.org/project/fastapi-limiter/ (Feb 2026 release)
- PyPI pyrate-limiter: https://pypi.org/project/pyrate-limiter/ (Mar 2026 release)
- PyPI limits: https://pypi.org/project/limits/ (Feb 2026 release)
- GitHub slowapi: https://github.com/laurentS/slowapi (1.9k stars, production usage)
- GitHub pyrate-limiter: https://github.com/vutran1710/PyrateLimiter (489 stars, active)

### MEDIUM Confidence
- FastAPI middleware patterns (common knowledge, verified through PyPI package README)
- Token bucket algorithm implementation (industry standard, textbook algorithm)

## Decision Summary

**Recommended:** Custom implementation using Python standard library

**Rationale:**
1. **Simplicity:** ~200-300 lines of code vs 1000s in external library
2. **Zero dependencies:** Uses stdlib + existing FastAPI/pydantic
3. **Perfect fit:** Token bucket algorithm matches requirements exactly
4. **Maintainability:** Owned code = easier debugging, no version conflicts
5. **Testing:** Direct unit tests vs mocking library internals
6. **Architecture:** Integrates cleanly with existing patterns (middleware, pydantic-settings, domain exceptions)

**When to reconsider:** Multi-instance deployment, need for Redis persistence, distributed rate limiting

**Confidence:** HIGH - Decision based on current official package data, project requirements, and architectural analysis.
