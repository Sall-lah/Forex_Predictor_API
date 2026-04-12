# External Integrations

**Analysis Date:** 2026-04-12

## APIs & External Services

**Data Providers:**
- Kraken Public OHLC API - Fetch hourly OHLCV candles for forex/crypto pairs
  - Endpoint: `https://api.kraken.com/0/public/OHLC` (configurable via `KRAKEN_OHLC_URL`)
  - SDK/Client: `httpx` (HTTP GET calls in `api/app/shared/ohlcv/kraken_api.py`)
  - Timeout: Configurable via `KRAKEN_TIMEOUT` (default 15.0 seconds)
  - Auth: None required (public endpoint)

## Data Storage

**Databases:**
- None - API is stateless with no persistent database

**File Storage:**
- Local filesystem - ML model artifact at `api/app/features/prediction/ml_models/lightgbm_model_forex.pkl`
- Loaded via `joblib` in `ModelLoader.get_model()` (`api/app/features/prediction/service.py`)

**Caching:**
- In-process memory caching only:
  - Settings singleton via `functools.lru_cache` in `api/app/core/config.py`
  - ML model singleton via `ModelLoader` thread-safe pattern in `api/app/features/prediction/service.py`
  - Rate limit state in `InMemoryRateLimitStorage._states` (`api/app/middleware/rate_limit/storage.py`)

## Authentication & Identity

**Auth Provider:**
- None - API exposes public endpoints without authentication
- Rate limiting enforced via `RateLimitMiddleware` (`api/app/middleware/rate_limit/middleware.py`)

## Monitoring & Observability

**Error Tracking:**
- None - no external error tracking service

**Logs:**
- Python standard library `logging` module
- Configured in `api/app/main.py` with format: `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`
- Log level controlled by `LOG_LEVEL` environment variable (default: `info`)

## CI/CD & Deployment

**Hosting:**
- Not detected - no hosting configuration files found

**CI Pipeline:**
- None - no CI/CD configuration files detected at `api/` root

## Environment Configuration

**Required env vars:**
- `ENVIRONMENT` - Application environment (development/production)
- `LOG_LEVEL` - Logging level (debug/info/warning/error)
- `API_VERSION` - API version string
- `API_PREFIX` - API route prefix (default: `/api/v1`)
- `KRAKEN_OHLC_URL` - Kraken OHLC endpoint URL
- `KRAKEN_TIMEOUT` - HTTP request timeout in seconds
- `KRAKEN_HOURLY_INTERVAL` - OHLC interval in minutes
- `KRAKEN_DEFAULT_HOURS` - Default lookback hours for OHLC data
- `MODEL_DIR` - Directory containing model artifacts
- `MODEL_FILENAME` - Model artifact filename
- `PREDICTION_FETCH_HOURS` - Hours of data to fetch for predictions
- `MIN_ROWS_FOR_FEATURES` - Minimum rows required for feature extraction
- `RATE_LIMIT_DEFAULT_CAPACITY` - Default rate limit capacity
- `RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND` - Default refill rate
- `RATE_LIMIT_PREDICTION_CAPACITY` - Prediction endpoint capacity
- `RATE_LIMIT_HISTORICAL_CAPACITY` - Historic data endpoint capacity
- `RATE_LIMIT_STORAGE_MAX_ENTRIES` - Max entries in rate limit storage
- `RATE_LIMIT_STORAGE_TTL_SECONDS` - TTL for rate limit entries

**Example file:**
- `api/.env.example` contains all configuration options with defaults

**Secrets location:**
- No external secrets management - all config via environment variables or `.env` file

## Webhooks & Callbacks

**Incoming:**
- None - API accepts only direct client HTTP requests

**Outgoing:**
- None - API does not make outbound webhook calls

---

*Integration audit: 2026-04-12*