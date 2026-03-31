# Feature Landscape: API Rate Limiting

**Domain:** Production-ready API rate limiters
**Researched:** 2026-03-31
**Overall confidence:** HIGH

## Table Stakes

Features users expect. Missing = product feels incomplete or unprofessional.

| Feature | Why Expected | Complexity | Notes | Sources |
|---------|--------------|------------|-------|---------|
| **HTTP 429 Status Code** | Industry standard response when rate limited | Low | Universally expected behavior. Client libraries recognize 429 automatically. | GitHub, Stripe, IETF RFC 6585 |
| **X-RateLimit-Limit Header** | Communicates maximum requests allowed | Low | Part of de facto standard. Tells clients the configured limit. | GitHub (x-ratelimit-limit), Stripe, IETF draft-ietf-httpapi-ratelimit-headers |
| **X-RateLimit-Remaining Header** | Shows requests left in current window | Low | Critical for client throttling logic. Missing = blind clients. | GitHub (x-ratelimit-remaining), Stripe, IETF draft |
| **X-RateLimit-Reset Header** | Indicates when quota resets (epoch seconds or seconds until reset) | Low | Prevents thundering herd. Clients need this to know when to retry. IETF recommends seconds (not timestamp) to avoid clock sync issues. | GitHub (x-ratelimit-reset), Stripe, IETF draft |
| **Retry-After Header** | Tells clients exactly when to retry (in 429 response) | Low | HTTP standard. Should align with reset time. Rate limiters that omit this feel broken. | Stripe, AWS, RFC 9110 |
| **Per-IP Rate Limiting** | Basic abuse prevention without auth | Medium | Fundamental protection. Handles X-Forwarded-For for proxies. Beware: NAT can affect multiple users. | GitHub (60/hr unauthenticated), Stripe, AWS, Cloudflare |
| **Per-Endpoint Limits** | Different routes need different limits | Medium | /health vs /predict should have different quotas. Without this, expensive endpoints either get underprotected or cheap ones get over-restricted. | AWS (method-level), Stripe (endpoint-specific limits), Cloudflare |
| **Time Window Configuration** | Flexible window periods (seconds, minutes, hours) | Medium | Fixed 1-minute windows are too rigid. Need 10s for burst, 1h for sustained abuse. | Stripe (multiple windows), AWS, Cloudflare (10s-86400s), IETF draft |
| **Token Bucket Algorithm** | Handles bursts gracefully while enforcing average rate | High | Industry standard. Allows short bursts but prevents sustained abuse. Fixed window = bursty at boundaries. | AWS (explicitly token bucket), Stripe (implicit), Redis best practices |
| **Exempt Endpoints** | Exclude health checks, docs, static assets from limiting | Low | Monitoring tools will fail if /health is rate limited. Docs need to be always accessible. | Common practice (not explicitly in docs but implied) |
| **Clear Error Messages** | Descriptive JSON/text explaining why request was rate limited | Low | Generic "Too Many Requests" is frustrating. Should explain limit, remaining, and reset time. | Stripe (detailed error bodies), GitHub (error messages in responses) |

## Differentiators

Features that set product apart. Not expected, but highly valued.

| Feature | Value Proposition | Complexity | Notes | Sources |
|---------|-------------------|------------|-------|---------|
| **Multiple Time Windows** | Protects against both burst and sustained abuse | High | Example: 10/sec AND 100/min AND 1000/hr. Prevents attack vectors that exploit single-window gaps. Exposes closest-to-limit window. | GitHub (multiple windows), Stripe (10/sec + hourly limits), Cloudflare (multiple periods) |
| **X-RateLimit-Used Header** | Shows requests already consumed in window | Low | GitHub uses this. Helps debugging ("Did my last request count? How many times did the retry loop run?"). | GitHub (x-ratelimit-used) |
| **RateLimit-Policy Header** | Advertises policy parameters (limit;w=60) | Low | IETF standard. Tells clients the full policy (e.g., "100;w=60" = 100 per 60s). Eliminates guesswork. | IETF draft-ietf-httpapi-ratelimit-headers (RateLimit-Policy) |
| **Stripe-Rate-Limited-Reason Header** | Explains *which* limit was hit | Medium | "endpoint-rate" vs "global-rate" vs "resource-specific". Invaluable for debugging multi-limit policies. | Stripe (Stripe-Rate-Limited-Reason with enum values) |
| **Concurrency Limiting** | Caps simultaneous in-flight requests | High | Prevents slow-request attacks (100 concurrent 30s requests = DoS). Complements rate limiting. Separate concern from throughput. | GitHub (100 concurrent max), Stripe (concurrency limiter separate from rate) |
| **Per-User/API-Key Limits** | More granular than IP-based | Medium | Prevents one bad actor from affecting others on shared IP (corporate NAT, VPN). Requires auth system. | GitHub (5000/hr authenticated), AWS (usage plans per API key) |
| **Dynamic/Adaptive Limits** | Adjust limits based on server load | Very High | Lower limits during saturation. "We usually allow 100, but right now only 50." Prevents cascading failures. | Stripe (mentions adaptive throttling), AWS (best-effort, not guaranteed) |
| **Sliding Window** | More accurate than fixed window | High | Avoids boundary gaming (99 requests at :59, 100 at :00 = 199 in 2 sec). Token bucket approximates this. | IETF (sliding window vs fixed window discussion), Cloudflare |
| **Quota Reset Jitter** | Randomize reset times to prevent thundering herd | Low | If 10K clients all see reset=60, they all retry at :60. Add ±5s jitter to spread load. | IETF draft (explicit warning about thundering herd) |
| **Cache Exclusion** | Don't count cached responses against quota | Medium | If CDN serves from cache, shouldn't consume user's quota. Requires cache-aware architecture. | Cloudflare (cache exclusion feature on Business+ plans) |
| **Complexity-Based Limiting** | Weight expensive operations higher | Very High | Search query = 5 units, GET = 1 unit. More accurate resource protection than simple request count. | GitHub (search = separate limit, POST/mutation = 5 points), Cloudflare (complexity scoring on Enterprise) |
| **Request Throttling (vs Blocking)** | Delay requests instead of rejecting | High | When over limit, queue/delay instead of 429. Smoother UX. More complex to implement (needs queue, memory). | Cloudflare Enterprise (throttle vs block behavior), IETF (mentioned as advanced) |
| **Rate Limit Inspection Endpoint** | Dedicated GET /rate-limit endpoint | Low | Check remaining quota without consuming it. Useful for dashboards/monitoring. | GitHub (GET /rate_limit doesn't count against quota) |
| **Per-Resource Limits** | Different limits per object type | High | Example: 1000 updates/hour per PaymentIntent. Prevents single-resource hammering. | Stripe (PaymentIntent-specific limits, Subscription-specific limits) |
| **Rate Limit Warnings** | 200 response with low remaining value + warning header | Low | Proactive signal before hitting limit. "X-RateLimit-Remaining: 5" + "Warning: 199 - Approaching rate limit". | Not standard but best practice mentioned in IETF discussion |

## Anti-Features

Features to explicitly NOT build (at least in v1).

| Anti-Feature | Why Avoid | What to Do Instead | Sources |
|--------------|-----------|-------------------|---------|
| **Timestamp-Based Reset** | Clock skew between client/server causes confusion | Use seconds-until-reset (delay-seconds). More resilient to clock drift, no timezone issues. | IETF draft (explicit recommendation against timestamps) |
| **Rate Limit Dashboard UI** | Premature optimization, adds complexity | Expose via headers + inspection endpoint. Operators use config files. Dashboard = v2+ feature. | N/A (absence in all major APIs) |
| **Distributed Rate Limiting (v1)** | Requires Redis/distributed state, overkill for single instance | In-memory is sufficient for single-instance deployment. Add Redis when scaling to multiple instances. | Project constraint (single instance) |
| **Per-Method Granularity** | Too fine-grained, config explosion | Use per-endpoint (per route path). Methods usually share quotas (GET/POST /users = same resource). | AWS groups by resource, not by HTTP method |
| **Dynamic Quota Adjustment API** | Allows quota manipulation, security risk | Static config via env vars. Operators restart to change. Dynamic adjustment = complex auth + audit. | Stripe requires 6-week notice for large increases |
| **Burst Size Configuration** | Confuses users, token bucket abstraction leak | Derive burst from rate automatically (e.g., burst = rate * 2). Simpler mental model. | Not exposed in most APIs (implementation detail) |
| **Client-Side Rate Limiting** | Trusts client, easily bypassed | Always enforce server-side. Clients can *optionally* self-throttle using headers, but server is source of truth. | Security best practice |
| **Load Testing in Sandbox** | Sandbox limits != production limits, misleading | Mock API calls in load tests. Document that sandbox has lower limits. | Stripe (explicit anti-pattern in docs) |
| **Zero-Cost Retry Logic** | Retries consume quota, amplifies problems | Exponential backoff + jitter. Failed requests still count. Warn clients about retry costs. | Stripe (retries count toward quota), GitHub (integrations banned for ignoring limits) |

## Feature Dependencies

```
Token Bucket Algorithm
  └─> Per-IP Limiting (needs token buckets per IP)
       └─> Per-Endpoint Limiting (needs token buckets per IP per endpoint)
            └─> Multiple Time Windows (needs multiple buckets per IP per endpoint)

HTTP 429 Status Code
  └─> Retry-After Header (must appear together in 429 response)
  └─> X-RateLimit-* Headers (should appear together)

Per-User Limits
  └─> Requires: Authentication/API Key System (not in scope for v1)

Concurrency Limiting
  └─> Independent of rate limiting (different counters, can implement separately)

Dynamic/Adaptive Limiting
  └─> Requires: Load metrics collection + threshold policies
```

## MVP Recommendation

**Prioritize (must-have for production-ready v1):**

1. ✅ **Token bucket algorithm** — Foundation, handles bursts
2. ✅ **Per-IP identification** — Table stakes abuse prevention
3. ✅ **Per-endpoint limits** — Essential (predict ≠ health)
4. ✅ **Standard headers** — X-RateLimit-{Limit,Remaining,Reset} + Retry-After
5. ✅ **HTTP 429 responses** — With clear error messages
6. ✅ **Exempt endpoints** — /health, /docs, /openapi.json must work
7. ✅ **Time window configuration** — Env var configurable (10s, 60s, 3600s, etc.)

**Include if time permits (strong differentiators):**

8. ⭐ **RateLimit-Policy header** — IETF standard, minimal effort, high value
9. ⭐ **X-RateLimit-Used header** — GitHub pattern, helps debugging
10. ⭐ **Reset jitter** — Prevents thundering herd, simple to add

**Defer to v2 (valuable but not MVP-critical):**

- Multiple time windows (adds complexity, single window sufficient for v1)
- Concurrency limiting (different problem, can add later)
- Per-user/API-key limits (requires auth system)
- Dynamic/adaptive limits (needs metrics + complex policy)
- Inspection endpoint (nice-to-have, headers are sufficient)
- Complexity-based scoring (very complex, premature optimization)

**Never build (anti-features):**

- ❌ Timestamp-based reset headers
- ❌ Client-side rate limiting
- ❌ Distributed state in v1 (Redis)
- ❌ Dashboard UI in v1

## Feature Interaction Matrix

| Feature | Works With | Conflicts With | Notes |
|---------|-----------|----------------|-------|
| Token Bucket | All time windows, all scopes | Fixed Window (choose one) | Preferred algorithm |
| Per-IP Limiting | Per-Endpoint, Multiple Windows | Per-User (choose primary scope) | Can combine with careful design |
| Per-Endpoint Limits | All algorithms, all scopes | None | Essential layering |
| Multiple Time Windows | Token Bucket, Sliding Window | Increases state complexity | Need N buckets per client |
| Retry-After Header | Always safe | None | Should match X-RateLimit-Reset |
| Concurrency Limits | Independent of rate limits | None | Separate counter, orthogonal concern |
| Dynamic Limits | All features | Static configuration | More complex, harder to reason about |
| Sliding Window | Per-IP, Per-User | Fixed Window (choose one) | More accurate but costlier |

## Complexity Ratings Explained

- **Low**: <4 hours implementation, minimal testing surface
- **Medium**: 1-2 days implementation, moderate testing needs
- **High**: 3-5 days implementation, significant test coverage required
- **Very High**: 1+ weeks, deep expertise needed, extensive edge cases

## Sources

**Primary (HIGH confidence):**
- GitHub REST API Rate Limits: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- Stripe Rate Limits: https://stripe.com/docs/rate-limits
- AWS API Gateway Throttling: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html
- IETF RateLimit Headers Draft: https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-07.html
- Cloudflare Rate Limiting Rules: https://docs.cloudflare.com/waf/rate-limiting-rules/
- Redis Rate Limiting Best Practices: https://redis.io/glossary/rate-limiting/

**Secondary (MEDIUM confidence):**
- Industry observation: All major APIs use token bucket or sliding window (not fixed window)
- Security best practice: Server-side enforcement mandatory (OWASP, various sources)

## Confidence Assessment

| Feature Category | Confidence | Reason |
|-----------------|------------|--------|
| Table Stakes | HIGH | Consistent across all 5+ major APIs examined |
| HTTP Headers | HIGH | IETF draft + universal adoption (GitHub, Stripe, AWS) |
| Algorithms | HIGH | AWS explicitly names token bucket; Redis docs + IETF confirm |
| Differentiators | HIGH | Directly from vendor docs (Stripe headers, GitHub concurrency, Cloudflare features) |
| Anti-Features | MEDIUM-HIGH | Inferred from absence + IETF warnings + Stripe explicit anti-patterns |

## Gaps & Open Questions

**Resolved:**
- ✅ Which headers are standard? → X-RateLimit-{Limit,Remaining,Reset} + Retry-After
- ✅ Token bucket vs fixed window? → Token bucket (AWS, industry standard)
- ✅ Seconds vs timestamp for reset? → Seconds (IETF recommendation)

**Unresolved (for future research):**
- **Performance**: What's the overhead of per-IP-per-endpoint token buckets at 10K RPS? (Needs benchmarking)
- **Memory**: How much RAM for 1M unique IPs with 10 endpoints? (Need capacity planning)
- **Edge cases**: How to handle time adjustments (NTP, DST)? (Implementation detail)

## Implementation Notes for Roadmap

**Phase suggestions:**

1. **Phase 1: Core MVP** — Token bucket + per-IP + per-endpoint + standard headers + 429 responses
2. **Phase 2: Polish** — RateLimit-Policy header, X-RateLimit-Used, reset jitter, better error messages
3. **Phase 3: Advanced** — Multiple windows, concurrency limiting, inspection endpoint
4. **Phase 4: Scale** — Redis-backed storage for multi-instance, adaptive limits

**Testing priorities:**
- Happy path: Request under limit returns 200 with headers
- Limit exceeded: Returns 429 with Retry-After and correct remaining=0
- Bucket refill: After reset time, requests succeed again
- Concurrent requests: Race conditions don't allow over-limit
- Per-endpoint isolation: /predict limit doesn't affect /health
- Exempt endpoints: /health never returns 429
- Header accuracy: Remaining/reset values match actual state
- Clock edge cases: Works across minute/hour boundaries
- X-Forwarded-For: Correctly extracts real IP behind proxy

**Key architectural decision:**
Token bucket (not fixed window) is mandatory for production quality. Fixed window allows 2× burst at window boundaries (anti-pattern). All major APIs use token bucket or sliding window for this reason.
