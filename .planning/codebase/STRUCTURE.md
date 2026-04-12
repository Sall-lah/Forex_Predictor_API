# Codebase Structure

**Analysis Date:** 2026-04-12

## Directory Layout

```
Forex_Predictor_API/
├── api/                           # FastAPI application
│   ├── app/                       # Main application package
│   │   ├── main.py                # FastAPI app initialization
│   │   ├── api/                   # Router aggregation
│   │   ├── core/                  # Config and exceptions
│   │   ├── features/              # Feature modules
│   │   │   ├── historic_data/     # Historic data feature
│   │   │   └── prediction/        # ML prediction feature
│   │   ├── shared/                # Shared utilities
│   │   │   └── ohlcv/             # OHLCV data handling
│   │   └── middleware/            # HTTP middleware
│   │       └── rate_limit/        # Rate limiting
│   ├── tests/                     # Test suite
│   ├── requirements.txt           # Python dependencies
│   ├── pytest.ini                 # Test configuration
│   ├── environment.yml             # Conda environment
│   └── .env.example               # Environment template
└── .planning/                     # GSD planning artifacts
    └── codebase/                  # Codebase documentation
```

## Directory Purposes

### api/app/
- **Purpose:** Main application package containing all business logic
- **Contains:** FastAPI app initialization, routers, services, schemas, middleware
- **Key files:** `api/app/main.py`

### api/app/api/
- **Purpose:** Router aggregation layer that combines feature routers
- **Contains:** Central `api_router` that includes all feature routers with prefixes
- **Key files:** `api/app/api/router.py`

### api/app/core/
- **Purpose:** Core application utilities (configuration and exceptions)
- **Contains:** Settings with Pydantic, domain exception hierarchy
- **Key files:** `api/app/core/config.py`, `api/app/core/exceptions.py`

### api/app/features/
- **Purpose:** Feature modules representing distinct API capabilities
- **Contains:** Each feature has its own subdirectory with router, service, schemas
- **Structure per feature:**
  - `router.py` - FastAPI router with endpoints
  - `service.py` - Business logic orchestration
  - `schemas.py` - Pydantic request/response models

### api/app/features/historic_data/
- **Purpose:** Historic OHLCV data retrieval feature
- **Contains:** 
  - `api/app/features/historic_data/router.py` - GET /live endpoint
  - `api/app/features/historic_data/service.py` - HistoricDataService
  - `api/app/features/historic_data/schemas.py` - OHLCVRecord, HistoricDataResponse

### api/app/features/prediction/
- **Purpose:** ML-based price movement prediction feature
- **Contains:**
  - `api/app/features/prediction/router.py` - POST /predict endpoint
  - `api/app/features/prediction/service.py` - PredictionService, ModelLoader, OHLCVPreprocessor
  - `api/app/features/prediction/schemas.py` - PredictionRequest, PredictionResponse
  - `api/app/features/prediction/ml_models/` - Model artifacts directory

### api/app/shared/
- **Purpose:** Shared utilities reusable across features
- **Contains:** OHLCV data handling modules
- **Key files:** `api/app/shared/ohlcv/__init__.py`

### api/app/shared/ohlcv/
- **Purpose:** Kraken API client and OHLCV DataFrame utilities
- **Contains:**
  - `api/app/shared/ohlcv/kraken_api.py` - KrakenAPIClient HTTP wrapper
  - `api/app/shared/ohlcv/ohlc_dataframe.py` - OHLCVDataFrame parsing/validation

### api/app/middleware/
- **Purpose:** HTTP middleware for cross-cutting concerns
- **Contains:** Rate limiting implementation
- **Key files:** `api/app/middleware/rate_limit/__init__.py`

### api/app/middleware/rate_limit/
- **Purpose:** Token-bucket rate limiting with in-memory state
- **Contains:**
  - `api/app/middleware/rate_limit/middleware.py` - RateLimitMiddleware entry point
  - `api/app/middleware/rate_limit/service.py` - RateLimiterService orchestration
  - `api/app/middleware/rate_limit/bucket.py` - TokenBucket algorithm
  - `api/app/middleware/rate_limit/storage.py` - InMemoryRateLimitStorage
  - `api/app/middleware/rate_limit/schemas.py` - Typed data classes

### api/tests/
- **Purpose:** Test suite with feature and middleware tests
- **Contains:**
  - `api/tests/conftest.py` - Pytest fixtures and configuration
  - `api/tests/features/` - Feature-level tests
  - `api/tests/middleware/` - Middleware tests
  - `api/tests/core/` - Core utilities tests

## Key File Locations

### Entry Points
- `api/app/main.py`: FastAPI application bootstrap, middleware registration, exception handlers
- `api/app/api/router.py`: Central router aggregation under `/api/v1` prefix

### Configuration
- `api/app/core/config.py`: Settings class with all configuration via Pydantic
- `api/.env`: Environment variables (not committed)
- `api/.env.example`: Environment variable template

### Core Logic
- `api/app/features/prediction/service.py`: Prediction orchestration, model loading, feature extraction
- `api/app/features/historic_data/service.py`: Historic data fetch orchestration
- `api/app/shared/ohlcv/kraken_api.py`: Kraken HTTP client
- `api/app/shared/ohlcv/ohlc_dataframe.py`: OHLCV parsing and validation

### Middleware
- `api/app/middleware/rate_limit/middleware.py`: Rate limit enforcement middleware

## Naming Conventions

### Files
- Modules: `snake_case.py` (e.g., `kraken_api.py`, `rate_limit_service.py`)
- Test files: `test_*.py` (e.g., `test_service.py`, `test_middleware.py`)
- Package markers: `__init__.py` in each directory

### Directories
- Feature directories: `snake_case` (e.g., `historic_data`, `rate_limit`)
- Shared utilities: `snake_case` (e.g., `ohlcv`)

### Classes
- PascalCase for classes and Pydantic models (e.g., `PredictionService`, `RateLimitMiddleware`, `PredictionRequest`)

### Functions/Methods
- snake_case for functions and methods (e.g., `fetch_hourly_ohlcv()`, `_resolve_client_ip()`)
- `get_*` prefix for FastAPI dependency factories (e.g., `get_prediction_service()`, `get_settings()`)
- `_` prefix for private helper methods

### Variables
- snake_case for variables and attributes (e.g., `mock_kraken_payload`, `latest_features`)

## Where to Add New Code

### New Feature Module
- Create directory: `api/app/features/<feature_name>/`
- Required files:
  - `api/app/features/<feature_name>/__init__.py` (empty or re-exports)
  - `api/app/features/<feature_name>/router.py` (FastAPI routes)
  - `api/app/features/<feature_name>/service.py` (business logic)
  - `api/app/features/<feature_name>/schemas.py` (Pydantic models)
- Register in `api/app/api/router.py` with `include_router(..., prefix="/<feature_name>")`

### New Shared Utility
- If shared across features: `api/app/shared/<utility_name>/`
- If feature-specific: within feature directory

### New Middleware
- Create directory: `api/app/middleware/<middleware_name>/`
- Register via `app.add_middleware(...)` in `api/app/main.py`

### New Configuration
- Add to `Settings` class in `api/app/core/config.py`
- Use `Field(...)` with defaults for optional settings

### New Domain Exception
- Add class to `api/app/core/exceptions.py` inheriting from `BaseAppException`
- Add handler in `api/app/main.py` if special HTTP mapping needed

### Tests for New Feature
- Test file location: `api/tests/features/<feature_name>/test_*.py`
- Use fixtures from `api/tests/conftest.py`

## Special Directories

### api/app/features/prediction/ml_models/
- **Purpose:** Serialized ML model artifacts
- **Contents:** `lightgbm_model_forex.pkl` (LightGBM model)
- **Generated:** No (trained externally)
- **Committed:** Yes

### api/tests/
- **Purpose:** Pytest-based test suite
- **Structure:** Mirrors `api/app/` structure with tests
- **Generated:** No
- **Committed:** Yes

### __pycache__/
- **Purpose:** Python bytecode cache
- **Generated:** Yes (automatic)
- **Committed:** No (in `.gitignore`)

---

*Structure analysis: 2026-04-12*