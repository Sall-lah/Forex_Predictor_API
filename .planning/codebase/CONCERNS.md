# Codebase Concerns

**Analysis Date:** 2026-04-12

## Tech Debt

**No Lockfile for Dependencies:**
- Issue: `requirements.txt` contains unpinned versions (e.g., `fastapi`, `httpx`, `python-dotenv`)
- Files: `api/requirements.txt`, `api/environment.yml`
- Impact: Non-deterministic builds; deployment could pull incompatible versions
- Fix approach: Use `pip-compile` or `poetry` to generate `requirements.lock` with pinned versions

**No Type-Checking Configuration:**
- Issue: No `mypy.ini`, `pyproject.toml` with mypy config, or type stubs declared
- Files: Entire `api/app/` directory
- Impact: Type errors may go undetected; refactoring risks runtime failures
- Fix approach: Add `mypy` to dev dependencies with strict settings, fix revealed errors

**No Linting Enforcement:**
- Issue: No `.flake8`, `pylintrc`, or equivalent linting config present
- Files: Repository root, `api/` directory
- Impact: Code style inconsistencies; potential bugs from unused imports/variables
- Fix approach: Add `ruff` or `flake8` with recommended rules, integrate into pre-commit

## Known Bugs

**In-Memory Rate-Limit State Loss:**
- Symptoms: All clients receive fresh rate-limit buckets after server restart
- Files: `api/app/middleware/rate_limit/storage.py`, `api/app/middleware/rate_limit/middleware.py`
- Trigger: Any server restart/pod respawn
- Workaround: None currently; acceptable for development, problematic for production

**Model Artifact Missing Causes 503:**
- Symptoms: API returns 503 Service Unavailable if `lightgbm_model_forex.pkl` is unreadable
- Files: `api/app/features/prediction/service.py` (ModelLoader._load_model())
- Trigger: Missing file, permission error, or corrupted pickle
- Workaround: Ensure model file exists and is readable before deployment

## Security Considerations

**No Authentication/Authorization:**
- Risk: All endpoints are publicly accessible with no API key or token validation
- Files: `api/app/main.py`, `api/app/features/prediction/router.py`, `api/app/features/historic_data/router.py`
- Current mitigation: Rate limiting provides basic abuse prevention
- Recommendations: Add API key validation or OAuth2 for production deployment

**Path Traversal Risk in Model Path:**
- Risk: `model_path` property uses `expanduser()` which resolves `~` to user home
- Files: `api/app/core/config.py` (line 64)
- Current mitigation: Model path is relative to app directory in default config
- Recommendations: Validate resolved path stays within allowed directories

**No Input Sanitization Beyond Pydantic:**
- Risk: SQL/log injection possible if error messages include unsanitized user input
- Files: `api/app/main.py` (exception handlers log raw exception messages)
- Current mitigation: Structured error responses; no user input in error messages
- Recommendations: Ensure `exc.message` never contains raw user data

## Performance Bottlenecks

**Feature Extraction Computation:**
- Problem: `OHLCVPreprocessor` computes 60+ technical indicators per request
- Files: `api/app/features/prediction/service.py` (lines 227-382)
- Cause: Heavy use of `ta` library for momentum, trend, volatility indicators; rolling window calculations
- Improvement path: Cache precomputed features in Redis; precompute indicators during Kraken fetch

**Model Loading Latency:**
- Problem: First prediction request triggers lazy model load (joblib.load)
- Files: `api/app/features/prediction/service.py` (ModelLoader.get_model())
- Cause: Singleton loads model only on first access; no warm-up
- Improvement path: Add startup event to pre-load model during app startup

**In-Memory Storage Scaling:**
- Problem: Rate-limit storage holds up to 100k entries in memory
- Files: `api/app/middleware/rate_limit/storage.py`
- Cause: Default config allows 100k unique client IPs; memory grows linearly
- Improvement path: Add Redis-backed storage for multi-instance deployments

## Fragile Areas

**Prediction Service Dependency Chain:**
- Files: `api/app/features/prediction/service.py`
- Why fragile: Chain includes Kraken API → OHLCV parsing → Feature extraction → Model loading → Inference. Any step failure causes 503/502/422.
- Safe modification: Add circuit breaker around Kraken calls; fallback to cached data if available
- Test coverage: Unit tests for service methods exist; integration with live Kraken untested

**Rate-Limit Storage Eviction:**
- Files: `api/app/middleware/rate_limit/storage.py` (lines 32-35)
- Why fragile: When max entries reached, oldest entries are evicted via LRU; legitimate users may lose quota unexpectedly
- Safe modification: Add warning metrics before eviction; consider per-client quotas
- Test coverage: `tests/middleware/rate_limit/test_storage.py` covers eviction logic

## Scaling Limits

**Single-Instance Rate-Limit State:**
- Current capacity: 100,000 unique client keys per instance
- Limit: Horizontal scaling (multiple uvicorn workers) breaks rate limiting (each has independent memory)
- Scaling path: Move to Redis-backed storage; implement sticky sessions

**Kraken API Dependency:**
- Current capacity: Unbounded but constrained by Kraken rate limits and network latency
- Limit: Kraken outage = API failure (no fallback data source)
- Scaling path: Add redundant data source (alternative exchange API or cached historical data)

## Dependencies at Risk

**Unpinned FastAPI:**
- Risk: API contract may change in breaking way with version upgrade
- Impact: Routing, middleware, or OpenAPI generation could break
- Migration plan: Pin to specific version (e.g., `fastapi>=0.115,<1.0`)

**Unpinned Dependencies in requirements.txt:**
- Risk: `httpx`, `pandas`, `numpy`, `ta`, `joblib` have unpinned versions
- Impact: Runtime errors from incompatible API changes; hard to debug
- Migration plan: Generate lockfile with pip-compile

## Missing Critical Features

**No Caching Layer:**
- Problem: Every prediction request fetches fresh data from Kraken and recomputes features
- Blocks: High-traffic production use; rate limit abuse potential
- Fix: Add Redis cache for OHLCV data (TTL ~5 minutes) and precomputed features

**No Health Check for Dependencies:**
- Problem: `/health` returns healthy even if Kraken API is unreachable or model is missing
- Blocks: Container orchestrator cannot detect degraded state
- Fix: Extend `/health` to ping Kraken and verify model file exists

## Test Coverage Gaps

**Live Kraken Integration:**
- What's not tested: Actual HTTP calls to Kraken API (tests use mocks)
- Files: `api/app/shared/ohlcv/kraken_api.py`, `api/app/features/historic_data/service.py`
- Risk: API response format changes silently; network errors surface only in production
- Priority: Medium

**Rate-Limit Under Load:**
- What's not tested: Behavior with thousands of concurrent requests
- Files: `api/app/middleware/rate_limit/service.py`, `api/app/middleware/rate_limit/bucket.py`
- Risk: Bucket calculation errors under race conditions
- Priority: Medium

**Model Inference Path:**
- What's not tested: End-to-end prediction with real model artifact
- Files: `api/app/features/prediction/service.py` (_predict_probabilities, _align_and_validate_features)
- Risk: Model version mismatch with feature columns causes runtime errors
- Priority: High

---

*Concerns audit: 2026-04-12*