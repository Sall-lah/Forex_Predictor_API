# Token Bucket Rate Limiter for Forex Predictor API

## What This Is

A production-ready token bucket rate limiter for the Forex Predictor API that provides per-IP, per-endpoint rate limiting with clean architecture and comprehensive observability. Built as FastAPI middleware with modular design, full type safety, and environment-based configuration.

## Core Value

Protect API endpoints from abuse while maintaining excellent developer experience through clear error messages, proper HTTP headers, and predictable behavior.

## Requirements

### Validated

- [x] Documentation in AGENTS.md for future development *(Validated in Phase 3: Documentation & Integration)*
- [x] Environment-variable configuration for all rate limits *(Validated in Phase 3: Documentation & Integration)*
- [x] Per-endpoint limit overrides via configuration *(Validated in Phase 3: Documentation & Integration)*
- [x] Configurable exemptions for health checks, docs, and static endpoints *(Validated in Phase 3: Documentation & Integration)*

### Active

- [ ] Token bucket algorithm implementation with accurate refill logic
- [ ] Per-IP client identification with proper X-Forwarded-For handling
- [ ] Per-endpoint rate limit configuration (different limits per route)
- [ ] In-memory storage for rate limit state (single instance deployment)
- [ ] FastAPI middleware integration with automatic application to all routes
- [ ] 429 Too Many Requests responses with detailed error messages
- [ ] X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers
- [ ] Retry-After header in 429 responses
- [ ] Modular file structure in dedicated app/middleware/rate_limit/ directory
- [ ] Clean separation: bucket logic, storage abstraction, middleware layer
- [ ] Full type hints with Pydantic models for configuration
- [ ] Comprehensive test coverage: happy path, limit exceeded, bucket refill, concurrent requests
- [ ] Integration with existing domain exception patterns

## Current State

Phase 3 is complete: rate-limiter architecture flow, extension checklist, operator env-var configuration examples, and exemption anti-bypass guidance are documented and cross-referenced.

### Out of Scope

- Redis-backed storage — Single instance deployment means in-memory is sufficient; can be added later if multi-instance deployment needed
- Per-API-key limiting — No authentication system exists; focusing on IP-based for v1
- Metrics/monitoring endpoint — Production-ready UX doesn't require full observability yet; can add in v2
- Rate limit dashboard — Configuration via env vars is sufficient for operators
- Dynamic rate adjustment — Static limits are simpler and sufficient for v1

## Context

**Current State:**
- Forex Predictor API is a working FastAPI application with feature-based architecture
- No rate limiting currently exists (API is unprotected)
- Existing patterns: routers → services → schemas, domain exceptions, dependency injection
- Testing infrastructure uses pytest with fixtures and mocking
- Configuration via pydantic-settings and .env files

**Why Now:**
- Building proper API hygiene from the start (best practice)
- Want production-ready protection before expanding usage
- Clean code and structured organization are priorities

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
| Token bucket over fixed window | More forgiving for bursty traffic; industry standard (AWS, Stripe use it) | — Pending |
| Per-IP identification | Simpler than API keys; sufficient protection without auth system | — Pending |
| In-memory storage | Single instance deployment; acceptable to reset on restart; no external dependencies | — Pending |
| Per-endpoint limits | Expensive prediction endpoints need stricter limits than health checks | — Pending |
| Middleware + exemptions | Automatic protection for all routes; explicit exemptions for operational endpoints | — Pending |
| Environment configuration | Operators can tune limits without code changes; follows existing config pattern | — Pending |
| Modular middleware/ directory | Clean separation from features/; dedicated location for cross-cutting concerns | — Pending |

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
*Last updated: 2026-03-31 after Phase 3 completion*
