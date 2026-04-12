# Codebase Concerns

**Analysis Date:** 2026-04-12

## Tech Debt

**Monolithic Frontend Components:**
- Issue: Excessive file size indicates a violation of the Single Responsibility Principle and mixing of state management, UI, and business logic.
- Files: `web/src/pages/Dashboard.tsx`
- Impact: Makes testing, maintaining, and updating the primary application view difficult. Reduces component reusability.
- Fix approach: Refactor `Dashboard.tsx` by splitting it into smaller, focused components (e.g., separating the chart, metrics panel, controls, and moving state into custom hooks like `useMarketData.ts`).

**Heavy Service Layer in Prediction:**
- Issue: The service module is extremely large and handles too many responsibilities (data fetching orchestration, feature extraction, ML model loading, and prediction formatting).
- Files: `api/app/features/prediction/service.py`
- Impact: Increased cognitive load, harder unit testing, and risk of regressions when modifying one part of the prediction pipeline.
- Fix approach: Extract the feature engineering logic (`ta` usage, pandas transformations) into a dedicated preprocessing module and keep the service focused strictly on orchestration.

## Known Bugs

**Potential Concurrency Issues in Singleton Loaders:**
- Symptoms: Threading/concurrency blocks during initial model load under high load.
- Files: `api/app/features/prediction/service.py`
- Trigger: Multiple simultaneous prediction requests to the API immediately after startup before the model is fully loaded/cached.
- Workaround: Model caching helps, but lazy loading could block early concurrent requests.

## Security Considerations

**API Key and Rate Limiting Storage:**
- Risk: In-memory rate limiting state could lead to inconsistencies or memory leaks under sustained heavy load or distributed deployments (if scaled horizontally).
- Files: `api/app/middleware/rate_limit/storage.py`, `api/app/middleware/rate_limit/bucket.py`
- Current mitigation: Basic `InMemoryRateLimitStorage` exists.
- Recommendations: Migrate to a Redis-backed rate limiting storage for production readiness and scalability.

**CORS Configuration:**
- Risk: Cross-origin restrictions might be too permissive or improperly configured between the new `web/` frontend and `api/`.
- Files: `api/app/main.py`
- Current mitigation: Relies on FastAPI CORS middleware.
- Recommendations: Ensure strict origin validation explicitly allowing only the `web/` host in production.

## Performance Bottlenecks

**Heavy DataFrame Manipulations in Request Path:**
- Problem: Complex pandas operations (calculating technical indicators via `ta`) run synchronously on the main thread during prediction requests.
- Files: `api/app/features/prediction/service.py`
- Cause: Generating indicators over OHLCV data on every request.
- Improvement path: Pre-calculate indicators on a background task or use an optimized caching layer for historic OHLCV features, only computing the newest candles on the fly.

## Fragile Areas

**External API Dependencies:**
- Files: `api/app/shared/ohlcv/kraken_api.py`
- Why fragile: Tightly coupled to the exact shape and uptime of Kraken's public OHLC endpoint. Any schema change or rate limiting from Kraken will break the prediction pipeline.
- Safe modification: Introduce a circuit breaker and fallback caching. Ensure robust HTTP timeouts and retry mechanisms.
- Test coverage: Relying heavily on mocked Kraken responses.

## Missing Critical Features

**Production-Grade Persistence:**
- Problem: The application heavily relies on in-memory storage for rate limits and potentially model state.
- Blocks: Horizontal scaling. If deployed across multiple pods or workers, rate limiting will be isolated per worker.

## Test Coverage Gaps

**Frontend Testing:**
- What's not tested: The new `web/` directory lacks comprehensive unit and E2E testing compared to the `api/` directory.
- Files: `web/src/pages/Dashboard.tsx`, `web/src/components/Chart.tsx`
- Risk: UI regressions and state management bugs could slip into production unnoticed.
- Priority: High

---

*Concerns audit: 2026-04-12*