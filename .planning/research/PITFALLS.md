# Pitfalls Research: API Rate Limiting

**Domain:** Token bucket rate limiting for FastAPI middleware
**Researched:** 2026-03-31
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: X-Forwarded-For Header Spoofing

**What goes wrong:**
Attackers can spoof X-Forwarded-For headers to bypass IP-based rate limiting by pretending to be different clients. A single attacker can send thousands of requests with different forged IP addresses, making IP-based limiting completely ineffective. This is the #1 way rate limiters get bypassed in production.

**Why it happens:**
Developers trust client-provided headers without validation. The X-Forwarded-For header is set by proxies/load balancers but can be manipulated by clients if not properly configured. Many tutorials show naive implementations like `request.headers.get("X-Forwarded-For")` without explaining the security implications.

**How to avoid:**
1. **Never trust X-Forwarded-For directly from untrusted sources**
2. Use `request.client.host` from FastAPI (Socket IP) as fallback
3. If behind reverse proxy: Configure trusted proxy IPs and only parse X-Forwarded-For if request came from trusted proxy
4. Use rightmost-valid-IP strategy: Parse X-Forwarded-For from right to left, stopping at first untrusted IP
5. FastAPI example:
```python
def get_client_ip(request: Request, trusted_proxies: set[str]) -> str:
    """Extract client IP safely, preventing header spoofing."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    
    # If no proxy header, use socket IP
    if not forwarded_for:
        return request.client.host
    
    # Only trust X-Forwarded-For if request came from trusted proxy
    if request.client.host not in trusted_proxies:
        return request.client.host
    
    # Parse rightmost valid IP from trusted chain
    ips = [ip.strip() for ip in forwarded_for.split(",")]
    for ip in reversed(ips):
        if ip not in trusted_proxies:
            return ip
    
    return request.client.host
```

**Warning signs:**
- Rate limiting not working despite configuration
- Single IP bypassing limits with high request volume
- Log analysis shows many unique IPs with identical user agents/behavior patterns
- Testing with curl shows limits can be bypassed with `-H "X-Forwarded-For: 1.2.3.4"`

**Phase to address:**
Phase 1 (Foundation) — This is a critical security issue that must be correct from day one. Cannot be retrofitted without breaking existing behavior.

---

### Pitfall 2: Race Conditions in Distributed Token Bucket

**What goes wrong:**
Multiple concurrent requests arrive at the same microsecond, all read counter=19 (limit is 20), all increment to 20, all get approved. Result: 5-10 requests approved when only 1 should have passed. This "get-then-set" race condition allows burst attacks to bypass limits by sending highly concurrent requests.

**Why it happens:**
Naive implementations use non-atomic operations: `counter = get_counter(); counter += 1; set_counter(counter)`. Between get and set, other processes can read stale values. This is exacerbated in async frameworks like FastAPI where many requests process simultaneously.

**How to avoid:**
1. **Use atomic increment operations** — Redis INCR, database UPDATE ... RETURNING, or threading.Lock
2. **Wrap increment + expiry in transactions** (Redis MULTI/EXEC, database transactions)
3. **Example using Redis:**
```python
async def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """Atomic rate limit check using Redis."""
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    result = await pipe.execute()
    
    count = result[0]  # INCR returns new value
    return count <= limit
```
4. **For in-memory (single instance):** Use asyncio.Lock or threading.Lock around read-modify-write
5. **Never use:** `if get_count() < limit: increment()` — always atomic

**Warning signs:**
- Rate limits exceeded by ~2-5% during high concurrency
- Limits work fine during manual testing but fail under load testing
- Logs show same client exceeding limit by small margins (21/20, 22/20)
- `pytest -n auto` (parallel tests) causes rate limit tests to flake

**Phase to address:**
Phase 1 (Foundation) — Core algorithm must be correct. Unit tests with `threading` or `asyncio.gather()` concurrent requests should verify atomicity before deployment.

---

### Pitfall 3: Fixed Window Burst at Boundary

**What goes wrong:**
Attacker sends 20 requests at 12:00:59, then 20 more at 12:01:00. Fixed window sees 20 in minute ending :59 (OK) and 20 in minute starting :01 (OK), approving 40 requests in 2 seconds. This "boundary burst" doubles effective rate, making limits meaningless for bursty traffic.

**Why it happens:**
Fixed window algorithm resets counters at hard boundaries (top of minute/hour). Attackers exploit the reset by timing requests just before and after the boundary. Simple to implement but fundamentally flawed for security use cases.

**How to avoid:**
1. **Use sliding window or token bucket** instead of fixed window
2. **Sliding window approximation:** Weight previous window's count
```python
def sliding_window_check(current_count: int, previous_count: int, 
                         window_elapsed_pct: float, limit: int) -> bool:
    """Approximate sliding window using two fixed windows."""
    previous_weight = 1.0 - window_elapsed_pct
    estimated_count = (previous_count * previous_weight) + current_count
    return estimated_count <= limit
```
3. **Token bucket:** Naturally smooths bursts because tokens refill continuously, not at boundaries
4. **Never use:** Pure fixed window for security-critical endpoints (login, payment, etc.)

**Warning signs:**
- Traffic logs show spikes of exactly 2x limit at top of hour/minute
- Alert: "Rate limit exceeded" but logs show requests within each window individually respected limit
- Load testing with synchronized requests shows 2x throughput
- Timestamps in violation reports cluster at :00, :15, :30, :45 boundaries

**Phase to address:**
Phase 1 (Foundation) — Token bucket is already chosen in PROJECT.md decision table. Must implement correctly (continuous refill, not batch refill at intervals).

---

### Pitfall 4: Memory Leaks from Unbounded Storage

**What goes wrong:**
Rate limiter stores one entry per unique IP address. After 1 million unique visitors, memory consumption reaches gigabytes. Server crashes or gets OOM-killed. This is especially bad with spoofed IPs (attacker sends requests with random X-Forwarded-For values) or IPv6 (2^128 address space).

**Why it happens:**
Developers forget that dictionaries/hash maps grow without bounds. In-memory storage needs explicit cleanup. Redis EXPIRE handles this automatically, but Python `dict` does not. Each entry seems small (50-100 bytes), but millions of entries = GB of memory.

**How to avoid:**
1. **Always expire old entries** — Don't rely on process restart
2. **Use TTL for every key:**
```python
class InMemoryStorage:
    def __init__(self):
        self.buckets: dict[str, tuple[TokenBucket, float]] = {}
        # Value = (bucket, expiry_timestamp)
    
    async def cleanup_expired(self):
        """Background task to remove expired entries."""
        now = time.time()
        expired = [k for k, (_, exp) in self.buckets.items() if exp < now]
        for key in expired:
            del self.buckets[key]
    
    async def get_bucket(self, key: str, ttl: int) -> TokenBucket:
        now = time.time()
        if key in self.buckets:
            bucket, exp = self.buckets[key]
            if exp > now:
                return bucket
        
        # Create new bucket with expiry
        bucket = TokenBucket(...)
        self.buckets[key] = (bucket, now + ttl)
        return bucket
```
3. **Run periodic cleanup task:** `asyncio.create_task(cleanup_loop())`
4. **Set max size limit** as circuit breaker (e.g., max 100k entries, LRU eviction)
5. **Monitor memory usage** in production (alert if >80% of limit)

**Warning signs:**
- Memory usage grows monotonically over days/weeks
- Server becomes slow/unresponsive after running for extended period
- `docker stats` or `htop` shows high memory consumption
- OOM errors in logs: `MemoryError` or `Killed (signal 9)`
- Restart "fixes" the issue temporarily (clears memory)

**Phase to address:**
Phase 1 (Foundation) — Cleanup mechanism must be built into initial InMemoryStorage implementation. Adding later requires migration and risks backward compatibility.

---

### Pitfall 5: Exemption List Bypass

**What goes wrong:**
Developer exempts `/health` and `/docs` from rate limiting for operational reasons. Attacker discovers that expensive prediction endpoint is accessible via `/docs/predict` or `/health/../api/predict`. Exemption rules written as string prefix checks allow path traversal or overlapping routes to bypass protection.

**Why it happens:**
Simple string matching like `if path.startswith("/health")` doesn't account for:
- Trailing slashes: `/health/` vs `/health`
- Path normalization: `/health/../api/predict` resolves to `/api/predict` after routing
- Nested routes: `/api/health` vs `/health`
- Query parameters: `/api/predict?health=1`

**How to avoid:**
1. **Exact path matching for exemptions:**
```python
EXEMPTED_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}

def is_exempted(path: str) -> bool:
    # Normalize path first
    normalized = path.split("?")[0].rstrip("/")
    return normalized in EXEMPTED_PATHS
```
2. **Use route names instead of paths** (more robust):
```python
# In middleware
route = request.scope.get("route")
if route and route.name in EXEMPTED_ROUTES:
    return await call_next(request)
```
3. **Allowlist, not blocklist** — Explicitly mark exempted routes, assume everything else is limited
4. **Test edge cases:** Path traversal, double slashes, case sensitivity, trailing slashes

**Warning signs:**
- Rate limiting works for direct paths but fails for variations
- Logs show high traffic to "operational" endpoints
- `/health` endpoint receiving thousands of requests per second (should be occasional monitoring)
- Attacker reconnaissance: Multiple 404s with path variations before successful bypass

**Phase to address:**
Phase 1 (Foundation) — Exemption logic must be security-reviewed. Simple to get right initially, hard to fix after deployment (changes behavior).

---

### Pitfall 6: Shared Rate Limit State Across Endpoints

**What goes wrong:**
Developer implements global rate limiter: 100 req/min per IP across ALL endpoints. User legitimately browses product catalog (95 cheap GET requests), then tries to checkout (expensive POST). Rate limiter blocks checkout because user "used up" their quota on browsing. This creates terrible UX and doesn't protect expensive endpoints.

**Why it happens:**
Implementing per-endpoint limits is more complex than global limit. Developers take the easy path: one counter per IP. This treats all endpoints equally, but prediction API calls are 100x more expensive than health checks or static files.

**How to avoid:**
1. **Per-endpoint rate limit keys:**
```python
def make_rate_limit_key(ip: str, endpoint: str) -> str:
    """Separate counters per endpoint per IP."""
    return f"ratelimit:{ip}:{endpoint}"

# Usage
key = make_rate_limit_key(client_ip, request.url.path)
```
2. **Configure different limits per endpoint:**
```python
ENDPOINT_LIMITS = {
    "/api/predict": (10, 60),      # 10 req/min
    "/api/historical": (100, 60),  # 100 req/min
    "/health": (1000, 60),          # 1000 req/min
    "default": (60, 60),           # 60 req/min default
}
```
3. **Use route grouping** for similar endpoints:
```python
def get_endpoint_group(path: str) -> str:
    if path.startswith("/api/predict"):
        return "prediction"
    elif path.startswith("/api/historical"):
        return "data"
    else:
        return "default"
```
4. **Document limit headers per endpoint** (X-RateLimit-Limit should reflect current endpoint's limit, not global)

**Warning signs:**
- User complaints: "I got blocked for normal browsing"
- Rate limit hit after mixed endpoint usage but not single endpoint abuse
- Logs show rate limit triggered after total requests across different endpoints sum to limit
- Testing: Calling /health 99 times + /api/predict once gets blocked

**Phase to address:**
Phase 1 (Foundation) — PROJECT.md explicitly requires per-endpoint configuration. Must be in initial design (storage key schema, config structure).

---

### Pitfall 7: Inconsistent Rate Limit Headers

**What goes wrong:**
Response returns `X-RateLimit-Remaining: 5` but next request gets 429 (should have 5 remaining). Or `Retry-After: 30` but retrying after 30 seconds still gets blocked. Clients can't reliably implement backoff because server lies about state. SDK developers file bugs, API gets reputation for being "buggy."

**Why it happens:**
Headers calculated before request processing, but counter incremented during processing. Race conditions between header generation and counter update. Or headers use different time source than rate limiter (system clock vs monotonic clock). Or Retry-After calculated wrong (uses window start time instead of window end).

**How to avoid:**
1. **Atomic header calculation:**
```python
async def apply_rate_limit(bucket: TokenBucket):
    """Atomically consume token and calculate headers."""
    allowed, remaining, reset_time = bucket.consume()
    
    headers = {
        "X-RateLimit-Limit": str(bucket.capacity),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(int(reset_time)),
    }
    
    if not allowed:
        retry_after = int(reset_time - time.time())
        headers["Retry-After"] = str(max(1, retry_after))  # Never 0 or negative
        raise RateLimitExceeded(headers=headers)
    
    return headers
```
2. **Single source of truth:** Headers derived from same state as allow/deny decision
3. **Test time consistency:** `assert retry_after == reset_time - current_time`
4. **Use monotonic time** (`time.monotonic()`) for durations, not `time.time()` (can go backward with NTP)

**Warning signs:**
- Client-side retry logic fails despite following Retry-After
- Remaining count goes negative or doesn't match expected decrement
- Flaky tests around header values
- Bug reports: "Your API said I have 10 requests left but blocked me"

**Phase to address:**
Phase 1 (Foundation) — Headers are part of the contract. Must be correct initially (changing header semantics breaks clients).

---

### Pitfall 8: Time Synchronization Issues in Distributed Systems

**What goes wrong:**
Multi-node deployment where Node A thinks current time is 12:00:30 and Node B thinks it's 12:00:28 (2 second clock drift). User sends 10 requests to Node A (counters stored with timestamp 12:00:30), then 10 to Node B. Node B sees counters from "the future" and either rejects them as invalid or treats as separate windows, allowing double the rate.

**Why it happens:**
System clocks drift over time (typical: 1-2 seconds per day without NTP). In distributed systems, each node has its own clock. Rate limiters use timestamps to calculate windows, but clocks disagree. Redis `TIME` command helps but adds latency.

**How to avoid:**
1. **For single instance (PROJECT.md scope):** Non-issue, use local `time.time()`
2. **If scaling to multiple instances later:**
   - Use centralized timestamp source (Redis TIME command)
   - Use TTL-based expiry (Redis EXPIRE) instead of timestamp comparison
   - Implement clock drift detection and alerting
   - NTP sync required (but drift still happens)
3. **Relative time instead of absolute:**
```python
# Bad: Absolute timestamps
if current_time >= window_start + window_size:
    reset_window()

# Good: Elapsed time
elapsed = time.monotonic() - window_start_monotonic
if elapsed >= window_size:
    reset_window()
```
4. **Test with simulated clock skew** (mock time.time)

**Warning signs:**
- Rate limits behave differently across servers behind load balancer
- Burst of 429s when traffic shifts between nodes
- Rate limit counters "jump" forward or backward
- Logs show negative time calculations or future timestamps

**Phase to address:**
Phase 2 (Scaling) — Not relevant for Phase 1 (single instance). Document as "known limitation" requiring refactor for multi-instance deployment.

---

### Pitfall 9: Missing Error Handling for Storage Failures

**What goes wrong:**
Redis connection drops mid-request. Rate limiter tries to check counter, gets `ConnectionError`. Developer didn't handle this, so exception bubbles up, request returns 500 to user. Under sustained Redis outage, ALL API requests fail even though application logic is healthy. Rate limiter meant to protect API, instead brings it down.

**Why it happens:**
Developers test happy path (storage works) but not failure modes. Storage is assumed to be reliable. In production, networks partition, Redis restarts, connection pools exhaust. Rate limiter must degrade gracefully.

**How to avoid:**
1. **Fail-open strategy** (allow request if rate limiter is broken):
```python
async def check_rate_limit_safe(key: str, limit: int) -> bool:
    """Rate limit check with graceful degradation."""
    try:
        return await check_rate_limit(key, limit)
    except (ConnectionError, TimeoutError) as exc:
        logger.error("Rate limiter storage failure: %s - ALLOWING REQUEST", exc)
        metrics.increment("rate_limit.storage_failure")
        return True  # Fail open
```
2. **Fail-closed strategy** (deny request if uncertain — more secure):
```python
except StorageError:
    logger.error("Rate limiter failure - DENYING REQUEST")
    return False  # Fail closed
```
3. **Circuit breaker pattern:** After N consecutive storage failures, stop calling storage temporarily
4. **Health check integration:** Mark service unhealthy if rate limiter consistently failing
5. **Fallback to local state:** Temporary in-memory tracking if Redis unavailable

**Warning signs:**
- 500 errors spike during Redis restart/maintenance
- All requests fail despite application being healthy
- Logs show storage exceptions not caught
- Monitoring: No graceful degradation, binary healthy/dead

**Phase to address:**
Phase 1 (Foundation) — Error handling is part of production-ready. Must decide fail-open vs fail-closed policy before deployment (security vs availability tradeoff).

---

### Pitfall 10: Token Bucket Refill Logic Errors

**What goes wrong:**
Token bucket with capacity=20, refill=1 token/sec. After 10 seconds of inactivity, should have 20 tokens (10 refilled + 10 already there = 20, but capped at capacity). Implementation forgets to cap: bucket has 30 tokens, allowing burst of 30 requests. Or, refill calculation uses integer division: `tokens += int(elapsed / refill_rate)` but `elapsed=1.5, refill_rate=1` gives 1 token instead of 1.5.

**Why it happens:**
Token bucket math is subtle: Must handle partial tokens, cap at capacity, handle very long idle periods (overflow), handle very short periods (underflow). Float precision errors accumulate. Copy-paste code from tutorials often has off-by-one errors.

**How to avoid:**
1. **Correct refill formula:**
```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill_time = time.time()
    
    def refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill_time
        
        # Calculate tokens to add (float precision)
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        
        self.last_refill_time = now
    
    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens."""
        self.refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
```
2. **Always cap at capacity:** `min(capacity, tokens + refilled)`
3. **Use float arithmetic** for refill calculations (don't truncate to int)
4. **Test edge cases:**
   - Very long idle period (1 hour)
   - Very short period (0.001 seconds)
   - Exactly at capacity
   - Burst of requests at exactly refill rate

**Warning signs:**
- Burst limits higher than configured capacity
- Rate limit allows more requests than expected after idle period
- Flaky tests: "Expected 20 tokens but got 19.99999"
- Production metrics show >100% of limit being used

**Phase to address:**
Phase 1 (Foundation) — Core algorithm correctness. Must have comprehensive unit tests for refill logic before considering implementation done.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip distributed state sync | Simpler implementation, single-node only | Cannot scale to multiple instances without rewrite | MVP for single-instance deployment (PROJECT.md scope) |
| No cleanup task for in-memory storage | Less code, fewer moving parts | Memory leak after days/weeks, requires restart | NEVER - must have TTL/cleanup from day 1 |
| Global rate limit (ignore per-endpoint) | Simple config, one counter per IP | Poor UX, doesn't protect expensive endpoints | Only if all endpoints have similar cost |
| Trust X-Forwarded-For without validation | Works in development/testing | Trivial to bypass in production | Only if NOT behind proxy AND not internet-facing |
| Fixed window instead of sliding/token bucket | Easiest algorithm to implement | Vulnerable to boundary burst attacks | Only for non-security-critical limits (e.g., internal analytics) |
| Skip Retry-After header in 429 response | Less code, simpler response | Clients can't implement proper backoff | Only for internal APIs with controlled clients |
| No Redis persistence (in-memory only) | Faster, simpler setup | Lose all rate limit state on restart | Acceptable for MVP with infrequent restarts |
| Fail-closed on storage errors | More secure default | Takes down entire API if storage fails | Only if availability is less critical than security |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastAPI Middleware | Applying middleware globally causes /health to be rate-limited | Use conditional middleware or path exemptions in middleware logic |
| Redis INCR + EXPIRE | Calling EXPIRE after INCR (non-atomic) — if crash between them, key never expires | Wrap in MULTI/EXEC transaction or use Lua script |
| pytest-asyncio | Tests fail randomly with "RuntimeError: no running event loop" | Use `@pytest.mark.asyncio` and `pytest-asyncio` fixture properly |
| X-Forwarded-For parsing | Splitting on comma but not stripping whitespace: `"1.2.3.4, 5.6.7.8"` | `[ip.strip() for ip in header.split(",")]` |
| FastAPI dependency injection | Creating new storage instance per request (no shared state) | Use singleton dependency with `@lru_cache` or global instance |
| Time-based windows | Using `datetime.now()` which respects DST/timezone changes | Use `time.time()` (epoch seconds) or `time.monotonic()` (no clock adjustments) |
| Response headers | Setting headers after response sent (too late) | Add headers in middleware before `await call_next(request)` or in exception handler |
| asyncio.Lock | Lock not shared across requests (created per request) | Global lock or per-key lock stored in shared dictionary |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No index on rate limit keys in DB | Slow queries, high CPU | Use in-memory storage (Redis/local dict), not SQL database | >1000 requests/sec |
| Synchronous Redis calls | Request latency +5-10ms per check | Use async Redis client (aioredis) with FastAPI | >100 concurrent requests |
| Per-request cleanup of expired entries | CPU spike, slow responses | Background cleanup task (asyncio.create_task every 60s) | >10k entries in storage |
| Logging every rate limit check | Disk I/O bottleneck, slow responses | Log only violations/errors, use metrics for counts | >1000 req/sec |
| No connection pooling for Redis | Connection exhaustion, new TCP handshake per request | Use connection pool (aioredis default) | >100 req/sec |
| Unbounded storage growth | Memory exhaustion after days/weeks | TTL on all entries + max size limit with LRU eviction | >100k unique IPs |
| Serializing bucket state to JSON per request | CPU cost of serialize/deserialize | Keep buckets as objects in memory, only serialize for persistence | >1000 req/sec |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| No rate limit on auth endpoints | Credential stuffing / brute force attacks | Stricter limits on /login, /token (e.g., 5 req/min) |
| Same limit for authenticated vs anonymous | Authenticated users can exhaust quota, degrading experience | Higher limits for authenticated users (per-API-key) |
| No rate limit on password reset | Email bombing, account enumeration | Separate strict limit on /reset-password (e.g., 3 req/hour) |
| Rate limit bypassed via different HTTP methods | Attacker uses HEAD/OPTIONS instead of GET | Rate limit key includes method, or normalize methods |
| No CAPTCHA fallback after repeated violations | Automated bot attacks continue indefinitely | After N violations, require CAPTCHA to continue |
| Leaking information in 429 response | "User not found" vs "Rate limited" — reveals valid usernames | Same error message regardless of whether user exists |
| IPv6 bypass | Rate limit by IPv4, attacker switches to IPv6 | Normalize IPs (extract /64 prefix for IPv6) |
| No alerting on rate limit violations | Attacks go unnoticed for hours/days | Alert if single IP hits limit >10 times in 1 hour |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Cryptic 429 error message | User confused, doesn't know what they did wrong | "Too many requests. Please wait 30 seconds and try again." |
| No Retry-After header | Client retries immediately, making problem worse (thundering herd) | Always include Retry-After with accurate time |
| Blocking legitimate bursts | User uploads 10 images, all fail after 3rd image | Higher burst capacity (token bucket) or exempt specific endpoints |
| Rate limit resets mid-workflow | User starts checkout, hits limit halfway through | Group related endpoints into shared quota bucket |
| No differentiation for premium users | Paying customers hit same limits as free tier | Tiered rate limits based on user role/subscription |
| Rate limit triggered by automated monitoring | Internal health checks exhaust quota | Exempt monitoring IPs or use separate quota pool |
| Error doesn't explain which action was rate limited | "Rate limit exceeded" but user made requests to 5 different endpoints | Error message includes endpoint: "Too many requests to /api/predict" |
| No feedback before hitting limit | User gets blocked suddenly | Return warning header at 80% quota: "X-RateLimit-Warning: true" |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Rate limiter middleware:** Often missing exemption list verification — verify `/health` and `/docs` actually exempted, not just configured
- [ ] **Token bucket refill:** Often missing capacity cap — verify refill doesn't allow >capacity tokens after long idle
- [ ] **Per-IP tracking:** Often missing X-Forwarded-For spoofing protection — verify header validation with curl test
- [ ] **In-memory storage:** Often missing cleanup task — verify memory doesn't grow unbounded (run for 1 hour, check size)
- [ ] **429 response:** Often missing Retry-After header — verify header present with correct value
- [ ] **Concurrent requests:** Often missing atomic increment — verify with `pytest -n 10` or `asyncio.gather()` stress test
- [ ] **Configuration:** Often missing per-endpoint overrides — verify prediction endpoint has stricter limit than health check
- [ ] **Error handling:** Often missing storage failure handling — verify graceful degradation when Redis unavailable
- [ ] **Tests:** Often missing race condition tests — verify tests with threading/asyncio concurrent requests
- [ ] **Documentation:** Often missing operator runbook — verify env vars documented, troubleshooting guide exists

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| X-Forwarded-For spoofing exploit | HIGH | 1. Emergency: Block all requests with X-FF header from untrusted IPs 2. Deploy fix with trusted proxy validation 3. Audit logs for attack source 4. Consider temporary IP blocklist |
| Memory leak from unbounded storage | LOW | 1. Restart service (clears memory) 2. Deploy cleanup task 3. Add memory monitoring alert 4. Consider Redis migration if frequent |
| Rate limit bypassed via boundary burst | MEDIUM | 1. Emergency: Reduce limits by 50% temporarily 2. Deploy sliding window fix 3. No data migration needed 4. Communicate limit change to users |
| Race condition allowing overages | MEDIUM | 1. Add mutex/lock as hotfix (slower but correct) 2. Deploy atomic operations 3. Load test to verify fix 4. Possible user apology if billing affected |
| Storage failure causing 500s | LOW | 1. Decide fail-open or fail-closed policy 2. Deploy error handling 3. Add circuit breaker 4. Implement health check monitoring |
| Missing Retry-After causes thundering herd | MEDIUM | 1. Deploy header fix 2. Communicate to API consumers 3. Monitor for traffic spikes 4. Consider temporary backoff enforcement server-side |
| Exemption bypass via path traversal | HIGH | 1. Emergency: Remove exemptions (rate limit everything) 2. Deploy exact path matching fix 3. Security audit all exemption rules 4. Pen test for other bypasses |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| X-Forwarded-For spoofing | Phase 1 (Foundation) | Test: `curl -H "X-Forwarded-For: 1.2.3.4"` doesn't bypass limit |
| Race conditions (atomic ops) | Phase 1 (Foundation) | Test: `pytest -n 10` concurrent requests respect limit |
| Fixed window boundary burst | Phase 1 (Foundation) | Test: Token bucket refill is continuous, not batched |
| Unbounded storage growth | Phase 1 (Foundation) | Test: Memory usage stable after 1hr run with rotating IPs |
| Exemption list bypass | Phase 1 (Foundation) | Test: `/health/../api/predict` doesn't bypass limit |
| Shared rate limit across endpoints | Phase 1 (Foundation) | Test: 100 /health requests don't block /api/predict |
| Inconsistent headers | Phase 1 (Foundation) | Test: X-RateLimit-Remaining matches actual remaining count |
| Time sync issues (distributed) | Phase 2 (Scaling) | Not relevant for single-instance; defer to multi-node phase |
| Storage failure handling | Phase 1 (Foundation) | Test: Redis disconnect returns 429 (fail-closed) or 200 (fail-open) |
| Token bucket refill math | Phase 1 (Foundation) | Test: Edge cases (0.001s, 1hr idle, exactly at capacity) |

---

## Sources

**High Confidence:**
- OWASP Blocking Brute Force Attacks (official controls documentation) — https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks
- Stripe Rate Limits (production implementation reference) — https://stripe.com/docs/rate-limits
- Kong API Gateway Rate Limiting Deep Dive (algorithm analysis) — https://konghq.com/blog/engineering/how-to-design-a-scalable-rate-limiting-algorithm
- Redis Rate Limiting Best Practices (storage patterns) — https://redis.io/glossary/rate-limiting/

**Medium Confidence:**
- Token bucket algorithm (Wikipedia) — Common knowledge, verified by multiple authoritative sources
- X-Forwarded-For security issues — Documented in web security literature, common pen-test finding

**Pitfall Discovery Method:**
- Literature review of official documentation (Stripe, OWASP, Kong, Redis)
- Analysis of production-grade open-source implementations
- Common attack patterns from security research
- Performance anti-patterns from distributed systems literature

---

*Pitfalls research for: Token bucket rate limiting for FastAPI middleware*
*Researched: 2026-03-31*
*Target: Single-instance FastAPI deployment with in-memory storage*
*Scope: Pitfalls relevant to PROJECT.md requirements and constraints*
