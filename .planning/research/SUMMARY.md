# Project Research Summary

**Project:** Token Bucket Rate Limiter for Forex Predictor API
**Domain:** Production-ready API rate limiting middleware
**Researched:** 2026-03-31
**Confidence:** HIGH

## Executive Summary

This project requires a production-grade token bucket rate limiter for a FastAPI-based forex prediction API. Research strongly recommends **custom implementation using Python standard library** rather than external packages. The token bucket algorithm (not fixed window) is industry standard for handling bursts gracefully while preventing sustained abuse. All major APIs (GitHub, Stripe, AWS) use this approach.

The recommended architecture is a middleware-based pattern with five core components: (1) RateLimitMiddleware for request interception, (2) RateLimiterService for orchestration, (3) TokenBucket for algorithm implementation, (4) InMemoryStorage for state management, and (5) pydantic-settings for configuration. This approach requires zero new dependencies, provides full control over implementation, and integrates cleanly with the existing FastAPI architecture patterns already established in the codebase.

Key risks center around three critical security pitfalls that must be addressed in Phase 1: X-Forwarded-For header spoofing (attackers can bypass IP-based limits), race conditions in concurrent token bucket updates (allowing request bursts beyond configured limits), and memory leaks from unbounded storage growth (leading to server crashes after days of operation). All three have well-documented prevention strategies that must be implemented from day one—retrofitting security is significantly harder than building it correctly initially.

## Key Findings

### Recommended Stack

The research conclusively recommends **custom implementation** over external libraries (slowapi, fastapi-limiter, pyrate-limiter, limits). This is based on: (1) project's single-instance in-memory requirements don't justify library complexity, (2) token bucket algorithm is straightforward (~200-300 lines), (3) external libraries are designed for different use cases (fixed window, distributed systems), and (4) zero dependencies aligns with "production-ready with clean architecture" goals.

**Core technologies:**
- **Python stdlib (`dict`, `threading.RLock`, `time.monotonic`)**: In-memory storage with thread-safe atomic operations — zero dependencies, O(1) lookups, prevents clock-adjustment issues
- **FastAPI `BaseHTTPMiddleware`**: Request interception layer — native integration with request/response cycle, automatic application to all routes
- **pydantic-settings**: Configuration management — already in stack, consistent with existing `app/core/config.py` patterns
- **Token bucket algorithm**: Rate limiting core — industry standard (AWS, Stripe, GitHub), handles bursts gracefully unlike fixed window

**Alternatives rejected:**
- slowapi 0.1.9: Last updated Feb 2024, fixed-window focused, requires `limits` library, decorator-heavy API doesn't fit middleware pattern
- fastapi-limiter 0.2.0: Designed for Redis/distributed systems, overkill for single instance, adds `pyrate-limiter` dependency
- pyrate-limiter 4.1.0: Complex multi-backend abstraction (Redis, Postgres) unnecessary for in-memory use case
- limits 5.8.0: Provides fixed/moving/sliding window algorithms, not pure token bucket

### Expected Features

Research analyzed 5+ major API providers (GitHub, Stripe, AWS, Cloudflare, IETF standards) to identify table stakes vs differentiators.

**Must have (table stakes):**
- HTTP 429 status code with Retry-After header — universal client expectation, enables proper backoff
- X-RateLimit-{Limit, Remaining, Reset} headers — de facto standard, missing these makes API feel unprofessional
- Token bucket algorithm — handles bursts gracefully, prevents boundary gaming (fixed window vulnerability)
- Per-IP rate limiting with X-Forwarded-For support — fundamental abuse prevention
- Per-endpoint limits — expensive endpoints (ML predictions) need stricter limits than health checks
- Exempt endpoints — /health, /docs, /openapi.json must not be rate limited (breaks monitoring)
- Clear error messages — descriptive JSON explaining limit, remaining, reset time

**Should have (competitive differentiators):**
- RateLimit-Policy header — IETF standard, minimal effort, helps clients understand limits
- X-RateLimit-Used header — GitHub pattern, valuable for debugging ("how many times did my retry loop run?")
- Reset jitter — prevents thundering herd when all clients retry simultaneously at reset time

**Defer (v2+):**
- Multiple time windows (10/sec AND 100/min AND 1000/hr) — adds complexity, single window sufficient for MVP
- Concurrency limiting — orthogonal concern, separate from throughput rate limiting
- Per-user/API-key limits — requires authentication system not in scope
- Dynamic/adaptive limits — needs metrics collection + complex policy engine
- Complexity-based scoring — very complex, premature optimization

**Anti-features (never build):**
- Timestamp-based reset headers — client/server clock skew causes confusion, use seconds-until-reset
- Dashboard UI in v1 — premature optimization, expose via headers + config files
- Distributed state (Redis) in v1 — single instance in-memory sufficient per requirements
- Client-side rate limiting — easily bypassed, security theater

### Architecture Approach

The architecture follows a **middleware-based interception pattern** with on-demand token refill (no background jobs). Requests flow through: FastAPI app → RateLimitMiddleware → RateLimiterService → TokenBucket → InMemoryStorage. The token bucket calculates refill on each request based on elapsed time (`min(capacity, tokens + elapsed * refill_rate)`), eliminating scheduler complexity and scaling to millions of idle buckets with zero overhead.

**Major components:**
1. **RateLimitMiddleware (Component A)**: HTTP request interceptor — extracts client IP (with X-Forwarded-For validation), determines endpoint key, checks exemption list, enriches response with headers
2. **RateLimiterService (Component B)**: Decision orchestration — loads per-endpoint configuration with fallback to global defaults, coordinates between TokenBucket and Configuration
3. **TokenBucket (Component C)**: Algorithm core — calculates refill based on elapsed time, atomically updates state with thread lock, enforces capacity limits
4. **InMemoryStorage (Component D)**: State manager — thread-safe dict with `threading.RLock`, key format `(client_id, endpoint)`, must include TTL-based cleanup to prevent memory leaks
5. **Configuration (Component E)**: Policy store via pydantic-settings — per-endpoint overrides, global defaults, exemption patterns loaded from environment variables

**Key patterns:**
- **Storage abstraction layer**: Define `RateLimitStorage` ABC interface to enable future Redis migration without changing algorithm logic (testability + evolvability)
- **Per-endpoint configuration with fallback**: Parse env vars like `RATE_LIMIT_OVERRIDES = {"POST:/api/v1/prediction/predict": "10,60,5"}`, fall back to global defaults if endpoint not configured
- **Response header enrichment**: Always return X-RateLimit-* headers (even on 200 responses) for client transparency, calculated atomically with allow/deny decision to prevent inconsistencies

**Anti-patterns to avoid:**
- Fixed window without burst handling (boundary problem: 200 req at :59, 200 req at :01 = 400 in 2 sec)
- Per-request database lookup (5-50ms latency penalty + race conditions)
- Rate limiting in route handlers (not DRY, easy to forget new endpoints)
- Ignoring X-Forwarded-For when behind proxy (all requests share single quota)

### Critical Pitfalls

Research identified 10 pitfalls; these 5 are CRITICAL for Phase 1:

1. **X-Forwarded-For header spoofing** — Attackers spoof header with random IPs to bypass rate limits. Prevention: Only trust header if request came from trusted proxy IP, parse rightmost-valid-IP strategy, fall back to socket IP. Test with `curl -H "X-Forwarded-For: 1.2.3.4"` to verify bypass fails.

2. **Race conditions in token bucket updates** — Concurrent requests read counter=19, all increment to 20, all approved (5-10 requests pass when only 1 should). Prevention: Use atomic operations with `threading.Lock` for in-memory (or Redis INCR for distributed). Test with `pytest -n 10` concurrent requests or `asyncio.gather()`.

3. **Memory leaks from unbounded storage** — One entry per unique IP; after 1M visitors, memory reaches GB scale. Prevention: Every key must have TTL, run periodic cleanup task (`asyncio.create_task`), set max size limit as circuit breaker. Test by running 1 hour with rotating IPs, monitor memory growth.

4. **Exemption list bypass via path traversal** — Simple `path.startswith("/health")` allows `/health/../api/predict` bypass. Prevention: Exact path matching with normalization (strip query params, normalize slashes), prefer route names over string matching. Test edge cases: double slashes, case sensitivity, trailing slashes.

5. **Inconsistent rate limit headers** — Response says `X-RateLimit-Remaining: 5` but next request gets 429. Prevention: Calculate headers atomically with allow/deny decision, use single source of truth (same state read), never calculate headers separately from counter update. Test time consistency: `retry_after == reset_time - current_time`.

**Additional critical pitfalls (must be aware of):**
- Shared rate limit across endpoints (cheap GET requests consume quota for expensive POST)
- Fixed window boundary burst (token bucket already chosen, must implement continuous refill correctly)
- Token bucket refill math errors (forget capacity cap, integer truncation, float precision)
- Missing error handling for storage failures (fail-open vs fail-closed policy required)
- Time synchronization issues (only relevant for multi-instance deployment, defer to Phase 2)

## Implications for Roadmap

Based on combined research, the project naturally divides into 4 phases with clear dependency ordering:

### Phase 1: Core Rate Limiting (Foundation)
**Rationale:** Algorithm correctness and security must be established before any polish. Token bucket, atomic operations, and X-Forwarded-For validation are foundational—cannot be retrofitted without breaking changes.

**Delivers:** 
- Production-ready rate limiting middleware protecting all API endpoints
- Per-IP + per-endpoint token bucket implementation with thread-safe storage
- HTTP 429 responses with standard headers (X-RateLimit-*, Retry-After)
- Exemption list for operational endpoints (/health, /docs)

**Addresses (from FEATURES.md):**
- ✅ Token bucket algorithm (table stakes)
- ✅ Per-IP limiting with X-Forwarded-For validation (table stakes)
- ✅ Per-endpoint limits with configurable windows (table stakes)
- ✅ HTTP 429 + standard headers (table stakes)
- ✅ Exempt endpoints (table stakes)
- ✅ Clear error messages (table stakes)

**Avoids (from PITFALLS.md):**
- Critical: X-Forwarded-For spoofing (#1)
- Critical: Race conditions (#2)
- Critical: Memory leaks (#4)
- Critical: Exemption bypass (#4)
- Critical: Inconsistent headers (#7)
- Critical: Shared rate limit across endpoints (#6)
- Critical: Token bucket refill math errors (#10)

**Key implementation requirements:**
- Storage abstraction (RateLimitStorage ABC) enables testing + future Redis migration
- Cleanup task for TTL-based memory management (prevent unbounded growth)
- Comprehensive unit tests for: concurrent requests (race conditions), refill edge cases (0.001s, 1hr idle, exactly at capacity), X-Forwarded-For validation, exemption path matching
- Fail-open vs fail-closed policy decision for storage failures

### Phase 2: API Polish & Observability
**Rationale:** After core functionality proven correct and secure, add professional touches that improve developer experience and operational visibility. These features are low-complexity differentiators with high value.

**Delivers:**
- Enhanced HTTP headers for better client integration
- Improved error messages with context
- Monitoring/metrics integration
- Configuration validation and documentation

**Addresses (from FEATURES.md):**
- ⭐ RateLimit-Policy header (IETF standard, differentiator)
- ⭐ X-RateLimit-Used header (GitHub pattern, debugging aid)
- ⭐ Reset jitter (prevents thundering herd, simple to add)
- Enhanced error messages with endpoint-specific context

**Uses (from STACK.md):**
- Existing pydantic-settings for advanced config validation
- FastAPI exception handlers for richer error responses
- Logging integration for violation monitoring

**Implements (from ARCHITECTURE.md):**
- Metrics collection (violations per endpoint, storage size, latency)
- Health check integration (mark unhealthy if storage consistently failing)
- Operational runbook (troubleshooting guide, env var docs)

### Phase 3: Advanced Features
**Rationale:** After MVP proven in production, add sophisticated features that differentiate from basic rate limiters. These are valuable but not MVP-critical, and some have significant complexity.

**Delivers:**
- Multiple time windows per endpoint (10/sec AND 100/min)
- Concurrency limiting (separate from rate limiting)
- Rate limit inspection endpoint (GET /rate-limit)
- Enhanced configuration (complexity-based weighting as option)

**Addresses (from FEATURES.md):**
- Multiple time windows (differentiator, deferred from Phase 1)
- Concurrency limiting (differentiator, orthogonal to rate limits)
- Inspection endpoint (differentiator, zero-cost quota check)
- Warning headers at 80% quota (UX improvement)

**Complexity notes:**
- Multiple windows require N buckets per (client, endpoint) pair → increased memory + complexity
- Concurrency limiting uses separate counter, must be atomic with in-flight request tracking
- Both require careful testing for interaction effects

### Phase 4: Scalability (Multi-Instance)
**Rationale:** Only needed when scaling beyond single instance. Requires architectural changes (centralized state) that would over-engineer Phase 1. Clear migration path documented in ARCHITECTURE.md.

**Delivers:**
- Redis-backed storage for distributed rate limiting
- Eventually consistent pattern for low-latency (Stripe approach)
- Clock drift handling and NTP requirements
- Configuration toggle: `RATE_LIMIT_STORAGE_TYPE=redis` vs `memory`

**Avoids (from PITFALLS.md):**
- Time synchronization issues (#8) — only relevant for multi-instance
- Distributed race conditions (Redis Lua scripts for atomic ops)

**Architecture changes:**
- Implement `RedisStorage` class with same `RateLimitStorage` interface (abstraction pays off)
- Use Redis MULTI/EXEC or Lua script for atomic increment + expire
- Add circuit breaker for Redis failures
- Optional: Eventually consistent mode (in-memory cache + periodic sync)

**When to implement:** Only when horizontally scaling (Kubernetes with 2+ replicas, load balancer). Single instance should stay in-memory per research findings.

### Phase Ordering Rationale

**Why Foundation → Polish → Advanced → Scalability:**

1. **Correctness before features**: Token bucket algorithm must be mathematically correct before adding headers or multi-window complexity. Refill math errors (Pitfall #10) are much harder to debug when mixed with feature code.

2. **Security cannot be retrofitted**: X-Forwarded-For validation, atomic operations, and exemption bypass prevention must be correct from day one. Changing these later breaks client behavior and may mask security issues.

3. **Defer complexity until validated**: Multiple time windows and concurrency limiting add significant state complexity. Only implement after single-window version proven in production.

4. **Scalability when needed**: Redis adds operational overhead (deployment, monitoring, connection management). Current project is single-instance—premature optimization would waste effort.

5. **Dependency graph respects interfaces**: Storage abstraction defined in Phase 1 enables clean Phase 4 Redis migration. Building Redis first would over-engineer the problem.

**Pitfall avoidance built into ordering:**
- Phase 1 addresses all 7 critical pitfalls before any feature work
- Phase 2 adds observability to detect runtime issues before scaling
- Phase 3 defers complexity until core is production-proven
- Phase 4 only when architectural constraint (single instance) changes

### Research Flags

**Phases likely needing deeper research during planning:**

- **Phase 3 (Advanced Features)**: Multiple time windows implementation — need to research memory-efficient bucket management strategies, interaction with refill logic. Stripe and GitHub mention this but don't publish implementation details. Consider `/gsd-research-phase` for concurrency limiting patterns (separate concern from rate limiting, less documented).

- **Phase 4 (Scalability)**: Redis Lua script atomicity patterns — while Redis docs cover this, distributed rate limiting has subtle edge cases (clock drift, network partitions, failover behavior). Consider `/gsd-research-phase` for production-grade distributed patterns.

**Phases with standard patterns (skip research-phase):**

- **Phase 1 (Foundation)**: Token bucket algorithm is well-documented (40+ years of research, Nginx/Stripe/AWS all publish approaches). In-memory storage with threading.Lock is Python stdlib standard. Middleware pattern is FastAPI core feature. Research already comprehensive.

- **Phase 2 (Polish)**: Headers are IETF standardized, metrics are FastAPI/Prometheus standard patterns. No novel research needed—implementation is straightforward application of standards.

**Research quality assessment:**
- Stack research: HIGH confidence (PyPI official data, current as of Feb-Mar 2026)
- Features research: HIGH confidence (GitHub, Stripe, AWS official docs)
- Architecture research: HIGH confidence (Nginx, Stripe blogs + FastAPI official docs)
- Pitfalls research: HIGH confidence (OWASP, production API docs, security research)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | Based on official PyPI data (Feb-Mar 2026 releases), project requirements analysis, and FastAPI architectural patterns. Custom implementation vs library decision is strongly supported by single-instance constraint and token bucket requirement. |
| Features | **HIGH** | Consistent feature set across 5+ major API providers (GitHub, Stripe, AWS, Cloudflare, IETF). Table stakes vs differentiators validated by universal adoption (HTTP 429, X-RateLimit-* headers) vs selective adoption (RateLimit-Policy, concurrency limits). |
| Architecture | **HIGH** | Core patterns verified across multiple production systems (Stripe scaling blog, AWS serverless patterns, Nginx implementation guide, Kong deep dive). Token bucket with on-demand refill is industry standard. FastAPI middleware integration is well-documented. Main uncertainty is distributed rate limiting (Redis Lua scripts), but single-instance scope makes in-memory storage HIGH confidence. |
| Pitfalls | **HIGH** | Critical pitfalls (#1-7) documented in OWASP controls, production API security advisories, and penetration testing literature. X-Forwarded-For spoofing and race conditions are well-known attack vectors. Memory leak patterns are common in long-running services. UX pitfalls validated by Stripe/GitHub public API changelogs (user complaints → feature changes). |

**Overall confidence:** **HIGH**

All four research areas have authoritative sources (official docs, production implementations, standards bodies). No major gaps or conflicting information. The recommendation (custom implementation with token bucket) is unanimous across sources. Pitfall prevention strategies are well-documented and testable.

### Gaps to Address

**Resolved during research:**
- ✅ Which rate limiting library to use? → None, custom implementation recommended
- ✅ Fixed window vs token bucket? → Token bucket (industry standard)
- ✅ Header naming conventions? → X-RateLimit-* (de facto standard)
- ✅ Reset header format (timestamp vs seconds)? → Seconds until reset (IETF recommendation)
- ✅ Middleware vs decorator pattern? → Middleware (fits FastAPI architecture)

**Unresolved (needs validation during Phase 1 implementation):**

- **Fail-open vs fail-closed policy**: When storage fails (Redis down, memory exhausted), should rate limiter allow requests (fail-open, better availability) or deny requests (fail-closed, better security)? Research shows both patterns used in production. **Decision point:** Phase 1 implementation must choose based on API criticality. Recommendation: Fail-closed for /api/predict (security-critical), fail-open for /api/historical (data retrieval).

- **Trusted proxy configuration**: Which IP addresses should be trusted for X-Forwarded-For parsing? **Decision point:** Phase 1 requires deployment environment knowledge. Recommendation: Make TRUSTED_PROXY_IPS configurable via env var, default to empty set (don't trust any proxies = safer default).

- **Memory limits for in-memory storage**: What is acceptable max memory usage for rate limit state? 100MB? 1GB? **Decision point:** Phase 1 needs capacity planning based on expected unique IPs. Recommendation: Set LRU eviction at 100k entries (~10MB) as circuit breaker, monitor in production.

- **Cleanup task frequency**: How often to run TTL-based cleanup? Every 60s? 300s? **Decision point:** Trade-off between memory efficiency and CPU overhead. Recommendation: Start with 60s intervals, tune based on profiling.

**Gaps requiring future research (not blocking):**

- **Performance at scale**: What's the overhead of per-IP-per-endpoint token buckets at 10K RPS? Needs load testing in Phase 1. Research provides architectural patterns but not performance benchmarks for this specific stack.

- **Redis failover behavior**: When Redis primary fails and replica promoted, are in-flight counters lost? Needs testing in Phase 4. Current research covers happy path, not failure modes.

- **IPv6 normalization**: Should rate limiting use full IPv6 address or /64 prefix to prevent address rotation bypass? Needs domain expertise consultation. Research mentions issue but doesn't provide definitive answer.

## Sources

### Primary (HIGH confidence)
- **PyPI slowapi** (https://pypi.org/project/slowapi/) — Library evaluation, last release Feb 2024
- **PyPI fastapi-limiter** (https://pypi.org/project/fastapi-limiter/) — Library evaluation, Feb 2026 release
- **PyPI pyrate-limiter** (https://pypi.org/project/pyrate-limiter/) — Library evaluation, Mar 2026 release
- **PyPI limits** (https://pypi.org/project/limits/) — Library evaluation, Feb 2026 release
- **GitHub API Rate Limits** (https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) — Feature expectations, header standards
- **Stripe Rate Limits** (https://stripe.com/docs/rate-limits) — Feature expectations, error patterns
- **Stripe Engineering Blog: Rate Limiters** (https://stripe.com/blog/rate-limiters) — Architecture patterns, sliding window
- **AWS API Gateway Throttling** (https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html) — Token bucket confirmation, per-method limits
- **IETF RateLimit Headers Draft** (https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-07.html) — Header standards, timestamp vs seconds
- **Cloudflare Rate Limiting Rules** (https://docs.cloudflare.com/waf/rate-limiting-rules/) — Feature benchmarking
- **Redis Rate Limiting Best Practices** (https://redis.io/glossary/rate-limiting/) — Storage patterns
- **Nginx Rate Limiting Blog** (https://blog.nginx.org/blog/rate-limiting-nginx) — Algorithm explanations
- **OWASP Blocking Brute Force** (https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks) — Security pitfalls
- **Kong Rate Limiting Deep Dive** (https://konghq.com/blog/engineering/how-to-design-a-scalable-rate-limiting-algorithm) — Architecture patterns
- **FastAPI Middleware Docs** (https://fastapi.tiangolo.com/tutorial/middleware/) — Integration patterns
- **Pydantic Settings Docs** (https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — Configuration patterns

### Secondary (MEDIUM confidence)
- Token bucket algorithm (Wikipedia + multiple authoritative cross-references) — Common knowledge, 40+ years of research
- X-Forwarded-For security issues — Web security literature, common penetration testing finding
- FastAPI middleware patterns — Community examples + official docs consensus

### Tertiary (LOW confidence)
- None — All findings verified with primary sources

**Research methodology:**
- Official documentation analysis (PyPI, GitHub, Stripe, AWS, IETF)
- Production implementation case studies (Stripe blog, Nginx blog, Kong blog)
- Security literature review (OWASP, penetration testing resources)
- Standards body specifications (IETF draft-ietf-httpapi-ratelimit-headers)
- Library ecosystem evaluation (PyPI packages, GitHub repositories)

---
*Research completed: 2026-03-31*  
*Ready for roadmap: yes*
