# Architecture

**Analysis Date:** 2026-04-12

## Pattern Overview

**Overall:** Monorepo Client-Server (React Frontend + Express Proxy + FastAPI Backend)

**Key Characteristics:**
- Unified monorepo structure with separated `api/` and `web/` directories.
- Frontend served via Express which acts as a static file server and API proxy.
- Backend FastAPI engine for ML prediction and data processing with a clear layered architecture.
- Rate limiting middleware on the backend.

## Layers

**Frontend (Client):**
- Purpose: Render user interface and trading dashboard.
- Location: `web/src/`
- Contains: React components, pages, hooks, services.
- Depends on: Express API Proxy.

**Express Server (Proxy/BFF):**
- Purpose: Serve React static files in production and proxy `/api` requests to the Python backend to avoid CORS and simplify deployment.
- Location: `web/server/`
- Contains: Express application, route definitions (`proxy.js`, `health.js`).
- Depends on: Internal network access to FastAPI backend.
- Used by: Frontend React App.

**API Router Aggregation (Backend):**
- Purpose: Aggregate backend feature routers into one central router under a versioned prefix.
- Location: `api/app/api/`
- Contains: `api_router` and `include_router(...)` calls.
- Depends on: `api/app/features/historic_data/router.py`, `api/app/features/prediction/router.py`.
- Used by: ASGI runtime in `api/app/main.py`.

**Feature Service Layer (Backend):**
- Purpose: Execute domain-specific workflows and coordinate shared modules.
- Location: `api/app/features/*/service.py`
- Contains: Service classes orchestrating business logic, data fetching, and inference.
- Depends on: `api/app/shared/ohlcv/`, `api/app/core/config.py`.
- Used by: Feature router endpoints via FastAPI Dependency Injection.

**Shared Infrastructure Layer (Backend):**
- Purpose: Isolate Kraken HTTP transport and OHLCV parsing logic.
- Location: `api/app/shared/ohlcv/`
- Contains: HTTP client wrapper and DataFrame utilities.
- Depends on: `httpx`, `pandas`.

**Middleware Layer (Backend):**
- Purpose: Enforce request rate limiting.
- Location: `api/app/middleware/rate_limit/`
- Contains: Token-bucket calculator, state storage, and middleware class.

## Data Flow

**Request-Response Flow (Prediction Endpoint):**
1. React frontend calls `/api/v1/prediction/predict`.
2. Express server proxy intercepts and forwards to `http://localhost:8000/api/v1/prediction/predict`.
3. FastAPI receives request, passes through Rate Limit Middleware.
4. `PredictionService` fetches live data via `KrakenAPIClient` and parses it into `OHLCVDataFrame`.
5. Features are calculated via `ta` library.
6. `ModelLoader` singleton provides LightGBM model for inference.
7. Prediction response travels back through proxy to client.

**State Management:**
- Frontend: React state/hooks.
- Backend Model: Process-level cached state in `ModelLoader._model`.
- Backend Rate Limit: Process-level in-memory state in `InMemoryRateLimitStorage._states`.

## Key Abstractions

**Service Layer Abstraction:**
- Purpose: Keep endpoint functions thin and move business workflow to testable classes.
- Examples: `api/app/features/prediction/service.py`
- Pattern: Router delegates to service instance injected via FastAPI `Depends()`.

**Model Loader Singleton:**
- Purpose: Load heavy ML model artifact lazily and reuse safely across requests.
- Examples: `ModelLoader` in `api/app/features/prediction/service.py`
- Pattern: Thread-safe singleton with double-checked locking.

## Entry Points

**Frontend Application:**
- Location: `web/src/main.tsx`
- Triggers: Browser loading the app.
- Responsibilities: React DOM rendering.

**Express Server:**
- Location: `web/server/index.js`
- Triggers: Node execution `node server/index.js`.
- Responsibilities: Listen on HTTP port, proxy `/api` routes, serve static assets.

**FastAPI Application:**
- Location: `api/app/main.py`
- Triggers: `uvicorn app.main:app --app-dir api`.
- Responsibilities: Bootstrap FastAPI, load middleware, expose endpoints.

## Error Handling

**Strategy:** Domain Exceptions mapped to HTTP Responses.

**Patterns:**
- Raise domain exceptions from service/adapter layers using `api/app/core/exceptions.py`.
- Map domain exceptions to HTTP responses in global handlers in `api/app/main.py`.
- Proxy layer (Express) passes through HTTP error status codes transparently to frontend.

## Cross-Cutting Concerns

**Logging:** Configured globally in `api/app/main.py` using Python `logging`.
**Validation:** Handled by Pydantic models at the API boundary in `api/app/features/*/schemas.py`.
**Authentication:** None currently enforced (public API with rate limiting).

---

*Architecture analysis: 2026-04-12*