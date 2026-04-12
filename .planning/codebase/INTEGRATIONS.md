# External Integrations

**Analysis Date:** 2026-04-12

## APIs & External Services

**Financial Data:**
- Kraken Public OHLC API - Used to fetch raw historical price data (Open, High, Low, Close, Volume)
  - SDK/Client: Direct HTTP via `httpx` (`api/app/shared/ohlcv/kraken_api.py`)
  - Auth: None (Public API endpoint)
  - Environment Configuration: `KRAKEN_OHLC_URL` (default: `https://api.kraken.com/0/public/OHLC`) in `api/app/core/config.py`

## Data Storage

**Databases:**
- None detected in the application.

**File Storage:**
- Local filesystem only - Used to store pre-trained Machine Learning model artifacts (`.pkl` files) in `api/app/features/prediction/ml_models/` (`api/app/features/prediction/service.py`)

**Caching:**
- In-memory only - The API rate-limiting token bucket uses a process-scoped singleton dictionary for state tracking (`api/app/middleware/rate_limit/storage.py`)
- Loaded model artifacts are cached in memory using Python's `functools.lru_cache` and class singletons (`api/app/features/prediction/service.py`)

## Authentication & Identity

**Auth Provider:**
- None - No user authentication or identity management is implemented.
- The system employs endpoint-level token bucket rate limiting to prevent abuse (`api/app/middleware/rate_limit/bucket.py`), not for identity validation.

## Monitoring & Observability

**Error Tracking:**
- None externalized. Application exceptions are mapped to HTTP responses globally (`api/app/main.py`).

**Logs:**
- Standard output (`logging` module) configured centrally via `api/app/main.py`.
- No external logging aggregators (e.g., Datadog, Sentry) are configured.

## CI/CD & Deployment

**Hosting:**
- Heroku / PaaS target implied - A `Procfile` is present at the project root for execution.
- Configured for multi-process environments leveraging tools like `concurrently` (`package.json`) and Express for static delivery (`web/server/index.js`).

**CI Pipeline:**
- None detected in the root or `.github/` directories.

## Environment Configuration

**Required env vars:**
- Environment variables are centrally managed by Pydantic (`api/app/core/config.py`)
- Key overrides (though defaults are provided):
  - `ENVIRONMENT`
  - `LOG_LEVEL`
  - `KRAKEN_OHLC_URL`
  - `MODEL_DIR`
  - Rate limiting constraints (e.g., `RATE_LIMIT_PREDICTION_CAPACITY`)

**Secrets location:**
- No critical secrets required for current public-only integrations.
- Local configuration is loaded from `.env` in `api/` via `python-dotenv` and `pydantic-settings`.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

---

*Integration audit: 2026-04-12*
