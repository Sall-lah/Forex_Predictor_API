# Roadmap: Token Bucket Rate Limiter

**Project:** Token Bucket Rate Limiter for Forex Predictor API
**Created:** 2026-03-31
**Granularity:** Coarse (3 phases, critical path only)
**Coverage:** 30/30 v1 requirements mapped ✓

## Phases

- [x] **Phase 1: Core Implementation** - Working rate limiter with token bucket, storage, middleware, and HTTP headers
- [x] **Phase 2: Testing & Security Validation** - Comprehensive test coverage including concurrency, security, and performance
- [x] **Phase 3: Documentation & Integration** - AGENTS.md updates, configuration guides, and production readiness

## Phase Details

### Phase 1: Core Implementation
**Goal**: Production-ready rate limiter middleware protecting all API endpoints with proper headers and configuration

**Depends on**: Nothing (first phase)

**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, HTTP-01, HTTP-02, HTTP-03, HTTP-04, HTTP-05, CONF-01, CONF-02, CONF-03, CONF-04, STOR-01, STOR-02, STOR-03, STRUC-01, STRUC-02, STRUC-03, STRUC-04, STRUC-05

**Success Criteria** (what must be TRUE):
  1. User sending 10 requests in 1 second to /api/predict receives 429 Too Many Requests after exceeding limit
  2. User receiving 429 response sees X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, and Retry-After headers with accurate values
  3. User can access /health, /docs, /redoc, and /openapi.json endpoints unlimited times without triggering rate limits
  4. User behind proxy has rate limits applied per their real IP address (via X-Forwarded-For), not proxy IP
  5. Operator can set different rate limits for /api/predict (10 req/min) vs /api/historical (100 req/min) via environment variables

**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Define rate-limit contracts and token bucket core
- [x] 01-02-PLAN.md — Add environment configuration and in-memory storage with cleanup
- [x] 01-03-PLAN.md — Wire FastAPI middleware with headers, exemptions, and 429 responses

**UI hint**: no

### Phase 2: Testing & Security Validation
**Goal**: Comprehensive test coverage proving rate limiter handles edge cases, prevents security bypasses, and performs under load

**Depends on**: Phase 1

**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07

**Success Criteria** (what must be TRUE):
  1. Developer running pytest sees 100% pass rate for happy path, limit exceeded, bucket refill, concurrent requests, and X-Forwarded-For spoofing tests
  2. Attacker attempting to spoof X-Forwarded-For header with random IPs is still rate limited by their actual socket IP
  3. System handling 10,000+ requests per second maintains accurate rate limit counts without race conditions (verified via asyncio.gather tests)
  4. Application running for 1+ hours with rotating IPs shows stable memory usage without unbounded growth (memory leak test passes)

**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md — Harden and validate functional + security rate-limit behavior
- [x] 02-02-PLAN.md — Add concurrency, load, and memory-stability validation harness

**UI hint**: no

### Phase 3: Documentation & Integration
**Goal**: Complete documentation enabling future developers to understand, configure, and extend the rate limiter

**Depends on**: Phase 2

**Requirements**: DOCS-01, DOCS-02, DOCS-03

**Success Criteria** (what must be TRUE):
  1. Developer reading AGENTS.md understands rate limiter architecture (middleware → service → bucket → storage), configuration patterns, and can add new per-endpoint limits
  2. Operator can configure per-endpoint rate limit overrides by following documented examples without reading source code
  3. Developer can identify which endpoints are exempt from rate limiting by reading exemption configuration guide

**Plans**: 1 plan

Plans:
- [x] 03-01-PLAN.md — Document architecture flow, configuration examples, and exemption security guidance

**UI hint**: no

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Implementation | 3/3 | Complete | 2026-03-31 |
| 2. Testing & Security Validation | 2/2 | Complete | 2026-03-31 |
| 3. Documentation & Integration | 1/1 | Complete | 2026-03-31 |

## Coverage Matrix

### Phase 1: Core Implementation (23 requirements)

**Core Rate Limiting:**
- CORE-01: Token bucket algorithm with continuous refill
- CORE-02: Per-IP client identification with X-Forwarded-For
- CORE-03: Per-endpoint rate limit configuration
- CORE-04: In-memory storage for rate limit state
- CORE-05: HTTP 429 Too Many Requests responses

**HTTP Headers & Responses:**
- HTTP-01: X-RateLimit-Limit header
- HTTP-02: X-RateLimit-Remaining header
- HTTP-03: X-RateLimit-Reset header
- HTTP-04: Retry-After header in 429 responses
- HTTP-05: Detailed JSON error message in 429 body

**Configuration & Integration:**
- CONF-01: FastAPI middleware integration
- CONF-02: Environment variable configuration
- CONF-03: Per-endpoint limit overrides
- CONF-04: Exemption list for operational endpoints

**Storage & State Management:**
- STOR-01: In-memory storage using Python dict
- STOR-02: Thread-safe atomic operations (asyncio.Lock)
- STOR-03: Memory cleanup with TTL for expired buckets

**File Structure & Code Quality:**
- STRUC-01: Dedicated middleware directory app/middleware/rate_limit/
- STRUC-02: Modular components (TokenBucket, InMemoryStorage, RateLimiter, Middleware)
- STRUC-03: Full type hints with Pydantic models
- STRUC-04: Clean separation (bucket logic, storage, service, middleware)
- STRUC-05: Integration with domain exception patterns

### Phase 2: Testing & Security Validation (7 requirements)

**Testing & Quality Assurance:**
- TEST-01: Happy path tests (requests within limit)
- TEST-02: Limit exceeded tests (429 responses with headers)
- TEST-03: Bucket refill tests (time-based token replenishment)
- TEST-04: Concurrent request tests (race condition prevention)
- TEST-05: X-Forwarded-For spoofing tests (security validation)
- TEST-06: Load/performance testing (10K+ requests per second)
- TEST-07: Memory leak testing (1+ hour run with rotating IPs)

### Phase 3: Documentation & Integration (3 requirements)

**Documentation:**
- DOCS-01: Update AGENTS.md with rate limiting architecture
- DOCS-02: Configuration examples in documentation
- DOCS-03: Exemption endpoint configuration guide

## Notes

**Granularity Rationale:**
Coarse setting drove aggressive compression from research-suggested 4 phases to 3 phases:
- Research Phase 1 (Foundation) + Phase 2 (Polish) → Roadmap Phase 1 (Core Implementation)
- Research Phase 3 (Advanced Features) → Deferred to v2 (out of scope for MVP)
- Research Phase 4 (Scalability) → Deferred to v2 (single instance constraint)

**Critical Pitfalls Addressed in Phase 1:**
All 5 critical security pitfalls from research must be prevented in Phase 1 implementation:
1. X-Forwarded-For spoofing (CORE-02 + TEST-05)
2. Race conditions in token bucket updates (STOR-02 + TEST-04)
3. Memory leaks from unbounded storage (STOR-03 + TEST-07)
4. Exemption list bypass via path traversal (CONF-04)
5. Inconsistent rate limit headers (HTTP-01, HTTP-02, HTTP-03 atomic calculation)

**Why 3 Phases:**
- Phase 1: Delivers working feature (implements 23/30 requirements = 77% of scope)
- Phase 2: Proves it's secure and performant (validates Phase 1 works correctly)
- Phase 3: Enables future maintenance (documents for next developer)

This compressed structure focuses on critical path: build → validate → document. No intermediate milestones that don't deliver user value.

---
*Last updated: 2026-03-31*
