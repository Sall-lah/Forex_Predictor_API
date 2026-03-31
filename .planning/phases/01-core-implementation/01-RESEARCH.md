# Phase 01 Research: Core Implementation

**Date:** 2026-03-31  
**Status:** Complete  
**Mode:** Standard research (requirements + existing architecture)

## Scope Investigated

- Token bucket implementation strategy for FastAPI middleware
- In-memory storage safety and cleanup strategy
- HTTP header behavior for rate-limited and non-limited responses
- Per-endpoint override configuration via `app/core/config.py`
- Secure client IP extraction with trusted proxy handling

## Existing Architecture Constraints (Must Follow)

1. Keep separation of concerns: middleware/router layers must not contain business logic.
2. Use domain exceptions from `app/core/exceptions.py` (no raw framework exceptions from service logic).
3. Use `Settings` in `app/core/config.py` with pydantic-settings for all tunables.
4. Preserve existing FastAPI app wiring in `app/main.py` and router aggregation in `app/api/router.py`.
5. Add no new dependencies (stdlib + existing FastAPI stack only).

## Technical Decisions for Phase 1 Planning

### 1) Algorithm
- Use token bucket with continuous refill (`elapsed_seconds * refill_rate_per_second`).
- Consume exactly 1 token per request.
- Return deny decision with computed retry seconds when tokens are insufficient.

### 2) Storage and Concurrency
- Implement in-memory storage with `dict[str, BucketState]` keyed by `{client_ip}:{endpoint_key}`.
- Protect mutating operations with `asyncio.Lock` to ensure atomic updates in async request concurrency.
- Add TTL cleanup method to prune stale buckets and bound memory growth.

### 3) Client Identification Security
- Parse `X-Forwarded-For` only if request source is in trusted proxies list.
- If source is not trusted, ignore `X-Forwarded-For` and use socket client host.
- Support empty trusted proxy list default (safer baseline).

### 4) HTTP Contract
- Apply `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` on limited endpoints for both pass/deny responses.
- Add `Retry-After` only on 429 responses.
- 429 body should include clear JSON payload with reason, endpoint, and retry_after_seconds.

### 5) Configuration
- Add global defaults plus per-endpoint overrides in `Settings`.
- Add explicit exempt paths (`/health`, `/docs`, `/redoc`, `/openapi.json`).
- Add trusted proxy and cleanup tuning env vars.

## Recommended File Design

Create `app/middleware/rate_limit/` with:

- `schemas.py` — config/state/decision models
- `bucket.py` — token bucket math
- `storage.py` — in-memory async storage
- `service.py` — orchestration (identify client, resolve limits, execute check)
- `middleware.py` — FastAPI middleware layer and response/header integration
- `__init__.py` — module marker/exports

## Risk Controls to Encode in Plans

1. **Header consistency:** calculate allow/deny + headers from a single decision object in one atomic path.
2. **Spoofing resistance:** trusted-proxy gate before reading `X-Forwarded-For`.
3. **Memory safety:** cleanup task + max entry guard.
4. **Operational safety:** exempt docs/health endpoints and ensure they bypass storage updates.

## Verification Targets for Planning

- Unit tests for bucket refill and deny behavior.
- Unit tests for storage atomicity semantics and cleanup pruning.
- Middleware tests for headers and 429 payload.
- Integration test for exempt paths never triggering rate limits.
- Config-driven test proving `/prediction` vs `/historic-data` can have different limits.

## Research Outcome

Phase is ready for executable planning. No additional external research is required for Phase 1.
