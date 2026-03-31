# Token Bucket Rate Limiter for Forex Predictor API

## What This Is

A production-ready token bucket rate limiter for the Forex Predictor API that provides per-IP, per-endpoint rate limiting with clean architecture and comprehensive observability. Built as FastAPI middleware with modular design, full type safety, and environment-based configuration.

## Core Value

Protect API endpoints from abuse while maintaining excellent developer experience through clear error messages, proper HTTP headers, and predictable behavior.

## Requirements

### Validated

- [x] Token bucket algorithm with accurate refill logic *(Validated in v1.0, Phase 1)*
- [x] Per-IP client identification with trusted-proxy-aware X-Forwarded-For handling *(Validated in v1.0, Phases 1-2)*
- [x] Per-endpoint rate-limit configuration (predict/historical/default policies) *(Validated in v1.0, Phases 1-3)*
- [x] In-memory rate-limit storage with async-safe atomic updates *(Validated in v1.0, Phases 1-2)*
- [x] FastAPI middleware integration for automatic global protection *(Validated in v1.0, Phase 1)*
- [x] HTTP 429 responses with structured JSON error body *(Validated in v1.0, Phase 1)*
- [x] X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers *(Validated in v1.0, Phases 1-2)*
- [x] Retry-After header on denied responses *(Validated in v1.0, Phase 1)*
- [x] Modular implementation in `app/middleware/rate_limit/` *(Validated in v1.0, Phase 1)*
- [x] Clear layer separation: middleware -> service -> bucket + storage *(Validated in v1.0, Phases 1-3)*
- [x] Full type hints and typed decision/config contracts *(Validated in v1.0, Phases 1-3)*
- [x] Security and performance test coverage (spoofing, concurrency, memory) *(Validated in v1.0, Phase 2)*
- [x] Documentation in AGENTS.md for architecture and extension checklist *(Validated in v1.0, Phase 3)*
- [x] Environment-variable configuration guide with per-endpoint overrides *(Validated in v1.0, Phase 3)*
- [x] Exemption endpoint and anti-bypass configuration guide *(Validated in v1.0, Phase 3)*

### Active

None for v1.0.

## Next Milestone Goals

- [ ] Improve operational observability (rate-limit events and metrics endpoints)
- [ ] Explore storage abstraction path toward Redis-backed distributed limiting
- [ ] Evaluate advanced headers (`RateLimit-Policy`, usage headers) for standards alignment
- [ ] Add regression guardrails for documentation/implementation drift in milestone transitions

## Current State

v1.0 is shipped and archived. The API has production-ready token-bucket rate limiting with:
- per-IP enforcement and trusted-proxy-aware client identity
- per-endpoint configurable limits and exempt-path handling
- consistent deny/allow headers and 429 contracts
- concurrency/performance/memory validation harnesses
- architecture and operator documentation for extension and operations

### Out of Scope

- Redis-backed storage — Single instance deployment means in-memory is sufficient; can be added later if multi-instance deployment needed
- Per-API-key limiting — No authentication system exists; focusing on IP-based for v1
- Metrics/monitoring endpoint — Production-ready UX doesn't require full observability yet; can add in v2
- Rate limit dashboard — Configuration via env vars is sufficient for operators
- Dynamic rate adjustment — Static limits are simpler and sufficient for v1

## Context

**Current State:**
- Forex Predictor API is protected by global rate-limit middleware and endpoint policy routing.
- Existing feature architecture is preserved (routers -> services -> schemas) while middleware remains a cross-cutting concern.
- Security and correctness safeguards are validated with focused middleware, bucket, storage, and performance tests.
- Configuration remains environment-driven through `app/core/config.py` and documented operator examples.

**Why Next:**
- v1.0 proves correctness and documentation quality; next focus is operational maturity and scale readiness.
- Future work should preserve current guarantees while improving observability and distributed deployment options.

**User Needs:**
- Per-endpoint flexibility (expensive prediction endpoints get stricter limits)
- Per-IP tracking (simple, no auth system required)
- Clear error messages when limits exceeded
- Easy configuration via environment variables
- Modular, maintainable code that follows existing patterns

**Technical Approach:**
- Token bucket algorithm (industry standard, handles bursts gracefully)
- Dedicated middleware directory: app/middleware/rate_limit/
- Components: TokenBucket class, InMemoryStorage, RateLimitMiddleware
- Integration via FastAPI middleware stack (runs before route handlers)
- Exemption list for /health, /docs, /openapi.json, /redoc

## Constraints

- **Tech Stack**: Python 3.12 + FastAPI — Must integrate with existing framework
- **Dependencies**: Only libraries in environment.yml — No Redis or external services
- **Architecture**: Must follow existing OOP patterns — Clean service classes, dependency injection, domain exceptions
- **Testing**: pytest with mocking — Comprehensive coverage required, no external dependencies in tests
- **Configuration**: pydantic-settings pattern — All limits configurable via .env
- **Deployment**: Single instance only — No distributed state management

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Token bucket over fixed window | More forgiving for bursty traffic; industry standard (AWS, Stripe use it) | ✓ Good (v1.0) |
| Per-IP identification | Simpler than API keys; sufficient protection without auth system | ✓ Good (v1.0) |
| In-memory storage | Single instance deployment; acceptable to reset on restart; no external dependencies | ✓ Good (v1.0, revisit for distributed v2) |
| Per-endpoint limits | Expensive prediction endpoints need stricter limits than health checks | ✓ Good (v1.0) |
| Middleware + exemptions | Automatic protection for all routes; explicit exemptions for operational endpoints | ✓ Good (v1.0) |
| Environment configuration | Operators can tune limits without code changes; follows existing config pattern | ✓ Good (v1.0) |
| Modular middleware/ directory | Clean separation from features/; dedicated location for cross-cutting concerns | ✓ Good (v1.0) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-31 after v1.0 milestone completion*
