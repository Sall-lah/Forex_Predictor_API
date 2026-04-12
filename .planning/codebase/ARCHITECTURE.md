# Architecture

**Analysis Date:** 2026-04-12

## Pattern Overview

**Overall:** Layered Service-Oriented Architecture with Dependency Injection

**Key Characteristics:**
- Clear separation between HTTP layer (routers), business logic (services), and shared infrastructure (shared modules)
- Dependency injection via FastAPI's `Depends()` mechanism for service instantiation
- Framework-agnostic domain exceptions decoupled from FastAPI HTTP concerns
- Singleton pattern for expensive resources (ML model loader)
- Token-bucket rate limiting with in-memory state management

## Layers

### Application Entry Point
- **Purpose:** Initialize the ASGI app, configure logging, register middleware, and wire global exception handlers
- **Location:** `api/app/main.py`
- **Contains:** `FastAPI(...)` app creation, `app.add_middleware(RateLimitMiddleware)`, `@app.exception_handler(...)`, `app.include_router(...)`, `/health` route
- **Depends on:** `api/app/core/config.py`, `api/app/core/exceptions.py`, `api/app/middleware/rate_limit/middleware.py`, `api/app/api/router.py`
- **Used by:** ASGI runtime (`uvicorn app.main:app`) and tests via `api/tests/conftest.py`

### API Router Aggregation
- **Purpose:** Aggregate feature routers into one central router under a versioned prefix
- **Location:** `api/app/api/router.py`
- **Contains:** `api_router` and `include_router(...)` calls for feature routers with prefix management
- **Depends on:** `api/app/features/historic_data/router.py`, `api/app/features/prediction/router.py`
- **Used by:** `api/app/main.py` through `app.include_router(api_router, prefix=settings.API_PREFIX)`

### Feature Router Layer
- **Purpose:** Define HTTP contracts and dependency injection boundaries per feature
- **Location:** 
  - `api/app/features/historic_data/router.py`
  - `api/app/features/prediction/router.py`
  - `api/app/features/historic_data/schemas.py`
  - `api/app/features/prediction/schemas.py`
- **Contains:** Endpoint declarations, request query/body parsing via Pydantic, response models, service factory functions (`get_service()`, `get_prediction_service()`)
- **Depends on:** Feature service modules and Pydantic schemas
- **Used by:** API composition layer in `api/app/api/router.py`

### Feature Service Layer
- **Purpose:** Execute feature-specific workflows and coordinate shared modules
- **Location:** 
  - `api/app/features/historic_data/service.py` (HistoricDataService)
  - `api/app/features/prediction/service.py` (PredictionService, ModelLoader, OHLCVPreprocessor)
- **Contains:** Service classes that orchestrate business logic, data fetching, preprocessing, and model inference
- **Depends on:** `api/app/shared/ohlcv/`, `api/app/core/config.py`, `api/app/core/exceptions.py`, model artifact path from `Settings.model_path`
- **Used by:** Feature router endpoints

### Shared Infrastructure Layer
- **Purpose:** Isolate Kraken HTTP transport and OHLCV parsing/validation logic for reuse across features
- **Location:** 
  - `api/app/shared/ohlcv/kraken_api.py` (KrakenAPIClient)
  - `api/app/shared/ohlcv/ohlc_dataframe.py` (OHLCVDataFrame)
  - Exported via `api/app/shared/ohlcv/__init__.py`
- **Contains:** HTTP client wrapper and DataFrame transformation utilities
- **Depends on:** `httpx`, `pandas`, `api/app/core/exceptions.py`, `api/app/core/config.py`
- **Used by:** `HistoricDataService` and `PredictionService`

### Middleware Layer
- **Purpose:** Enforce request rate limiting before route handlers execute
- **Location:** 
  - `api/app/middleware/rate_limit/middleware.py` (RateLimitMiddleware)
  - `api/app/middleware/rate_limit/service.py` (RateLimiterService)
  - `api/app/middleware/rate_limit/bucket.py` (TokenBucket)
  - `api/app/middleware/rate_limit/storage.py` (InMemoryRateLimitStorage)
  - `api/app/middleware/rate_limit/schemas.py` (RateLimitDecision, RateLimitPolicy, RateLimitState)
- **Contains:** Middleware, rate-limiter service, token-bucket calculator, in-memory state storage, typed policy/decision schemas
- **Depends on:** `starlette.requests.Request`, app settings from `api/app/core/config.py`
- **Used by:** Entire API surface through middleware registration in `api/app/main.py`

### Core Layer
- **Purpose:** Provide centralized typed settings and domain exception taxonomy
- **Location:** 
  - `api/app/core/config.py` (Settings, get_settings)
  - `api/app/core/exceptions.py` (BaseAppException and subclasses)
- **Contains:** Pydantic-based configuration with environment variable loading, domain exception hierarchy
- **Depends on:** `pydantic-settings` and environment variables
- **Used by:** All major layers in `api/app/`

## Data Flow

### Request-Response Flow (Prediction Endpoint)
1. Client sends POST to `/api/v1/prediction/predict`
2. RateLimitMiddleware evaluates request quota via RateLimiterService
3. Router layer validates request using Pydantic (PredictionRequest)
4. Router calls `service.predict(request)` - delegates to PredictionService
5. PredictionService fetches OHLCV data via KrakenAPIClient
6. OHLCVDataFrame parses and validates Kraken response
7. OHLCVPreprocessor extracts technical indicators and custom features
8. ModelLoader loads LightGBM model (singleton with lazy initialization)
9. Model predicts class probabilities (up/down/straight)
10. PredictionResponse returned to router, then to client
11. Global exception handlers catch any domain errors and map to appropriate HTTP status codes

### Request-Response Flow (Historic Data Endpoint)
1. Client sends GET to `/api/v1/historic-data/live?pair=BTC/USD`
2. RateLimitMiddleware evaluates request quota
3. Router validates query parameter via Pydantic
4. Router calls `service.fetch_hourly_ohlcv(pair)`
5. HistoricDataService fetches via KrakenAPIClient
6. OHLCVDataFrame parses and validates response
7. Response formatted with OHLCVRecord instances
8. HistoricDataResponse returned to client

**State Management:**
- Process-level cached model state in `ModelLoader._model` (`api/app/features/prediction/service.py`)
- Process-level in-memory rate-limit state in `InMemoryRateLimitStorage._states` (`api/app/middleware/rate_limit/storage.py`)
- Request-scoped service instances via FastAPI dependency injection

## Key Abstractions

### Service Layer Abstraction
- **Purpose:** Keep endpoint functions thin and move business workflow to testable classes
- **Examples:** `api/app/features/historic_data/service.py`, `api/app/features/prediction/service.py`
- **Pattern:** Router delegates to service instance; service returns typed schema objects

### Shared Module Abstraction
- **Purpose:** Reuse transport/parsing across features without duplicating HTTP and DataFrame logic
- **Examples:** `api/app/shared/ohlcv/kraken_api.py`, `api/app/shared/ohlcv/ohlc_dataframe.py`
- **Pattern:** Compose KrakenAPIClient + OHLCVDataFrame in feature services

### Model Loader Singleton
- **Purpose:** Load model artifact lazily and reuse it safely across requests
- **Examples:** `ModelLoader` in `api/app/features/prediction/service.py`
- **Pattern:** Thread-safe singleton with double-checked locking and explicit cache clearing

### Rate Limiter Pipeline
- **Purpose:** Separate transport interception, policy resolution, token math, and storage concerns
- **Examples:** 
  - `api/app/middleware/rate_limit/middleware.py` (entry point)
  - `api/app/middleware/rate_limit/service.py` (orchestration)
  - `api/app/middleware/rate_limit/bucket.py` (token calculation)
  - `api/app/middleware/rate_limit/storage.py` (state persistence)
- **Pattern:** Middleware delegates to service; service delegates to bucket + storage

## Entry Points

### Main Application
- **Location:** `api/app/main.py`
- **Triggers:** `uvicorn app.main:app --app-dir api`
- **Responsibilities:** Bootstrap FastAPI app, install middleware, register global exception handlers, mount API router, expose health endpoint

### API Router
- **Location:** `api/app/api/router.py`
- **Triggers:** Included from `api/app/main.py`
- **Responsibilities:** Register feature router modules under `/historic-data` and `/prediction` prefixes

### Feature Routers
- **Location:** 
  - `api/app/features/historic_data/router.py`
  - `api/app/features/prediction/router.py`
- **Triggers:** Client HTTP calls to `/api/v1/historic-data/live` and `/api/v1/prediction/predict`
- **Responsibilities:** Validate inputs, resolve service dependencies, return typed response schemas

## Error Handling

**Strategy:** Domain exception hierarchy with global handlers in main.py

**Patterns:**
1. Services raise framework-agnostic exceptions (`DataFetchError`, `DataValidationError`, `InsufficientDataError`, `ModelNotLoadedError`) from `api/app/core/exceptions.py`
2. Global exception handlers in `api/app/main.py` map domain exceptions to HTTP status codes:
   - `ModelNotLoadedError` → 503 Service Unavailable
   - `DataFetchError` → 502 Bad Gateway
   - `DataValidationError` → 422 Unprocessable Entity
   - `InsufficientDataError` → 422 Unprocessable Entity
   - `BaseAppException` catch-all → 500 Internal Server Error
3. Root cause preserved with exception chaining (`raise ... from error`) in shared and service layers

## Cross-Cutting Concerns

**Logging:** 
- Configured in `api/app/main.py` using `logging.basicConfig(...)` with settings from `api/app/core/config.py`
- Module loggers via `logger = logging.getLogger(__name__)` in service modules
- Logs lifecycle milestones and counts rather than raw payloads

**Validation:**
- Pydantic schemas at HTTP boundary (`api/app/features/*/schemas.py`)
- Domain validation in services raises custom exceptions
- OHLCVDataFrame provides column and row-count validation

**Authentication:**
- Not implemented (public API with rate limiting)

---

*Architecture analysis: 2026-04-12*