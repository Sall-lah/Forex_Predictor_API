# Rate Limiting Architecture

**Domain:** Token Bucket Rate Limiter for FastAPI
**Researched:** 2026-03-31

## Recommended Architecture

A rate limiting system consists of multiple cooperating components organized into distinct layers, from request interception through state management to enforcement decisions. The architecture follows a middleware pattern integrated into the FastAPI request-response cycle.

```
┌─────────────────────────────────────────────────────────────┐
│                      Request Flow                            │
└─────────────────────────────────────────────────────────────┘

HTTP Request
    │
    ▼
┌─────────────────────┐
│  FastAPI            │
│  Application        │
│  (main.py)          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Middleware Stack   │
│  (Order matters!)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Rate Limit          │◄────── Component A: Request Interceptor
│ Middleware          │        - Extracts client ID (IP address)
│                     │        - Determines endpoint key
│                     │        - Checks exemption list
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Rate Limiter        │◄────── Component B: Decision Engine
│ Service             │        - Loads configuration for endpoint
│                     │        - Consumes token from bucket
│                     │        - Returns allow/deny + metadata
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Token Bucket        │◄────── Component C: Algorithm Core
│ Algorithm           │        - Calculates tokens to refill
│                     │        - Atomically updates state
│                     │        - Enforces capacity limits
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Storage             │◄────── Component D: State Manager
│ Abstraction         │        - In-memory dict for single instance
│ (InMemoryStorage)   │        - Key: (client_id, endpoint)
│                     │        - Value: (tokens, last_refill_time)
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Configuration       │◄────── Component E: Policy Store
│ Provider            │        - Per-endpoint limits
│ (Settings)          │        - Global defaults
│                     │        - Exemption patterns
└─────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Input | Output | Communicates With |
|-----------|---------------|-------|--------|-------------------|
| **RateLimitMiddleware** | HTTP request interception, response enrichment | FastAPI Request, Call Next | FastAPI Response with headers | RateLimiterService, FastAPI |
| **RateLimiterService** | Orchestration and decision logic | (client_id, endpoint) | RateLimitResult(allowed, remaining, reset_time) | TokenBucket, Configuration |
| **TokenBucket** | Token bucket algorithm implementation | (client_id, endpoint, max_tokens, refill_rate) | (allowed: bool, tokens_remaining: int) | Storage |
| **InMemoryStorage** | State persistence and retrieval | (key, value) or (key) | BucketState(tokens, last_refill) | None (leaf node) |
| **Configuration (Settings)** | Rate limit policy definitions | Environment variables | RateLimitConfig(rate, burst, window) | RateLimiterService |

### Data Flow

**Happy Path (Request Allowed):**

1. HTTP request arrives at FastAPI application
2. RateLimitMiddleware intercepts request before route handler
3. Middleware extracts client IP from `request.client.host` or `X-Forwarded-For` header
4. Middleware constructs endpoint key from `request.url.path` and `request.method`
5. Middleware checks exemption list (e.g., `/health`, `/docs`) → if exempt, skip to step 15
6. Middleware calls `RateLimiterService.check_limit(client_id, endpoint)`
7. Service retrieves configuration for endpoint from Settings (e.g., 10 req/sec, burst 20)
8. Service calls `TokenBucket.consume(client_id, endpoint, tokens=1)`
9. TokenBucket calls `Storage.get(key)` → retrieves `(tokens=5.0, last_refill=12:00:00)`
10. TokenBucket calculates elapsed time since last refill (current_time - last_refill)
11. TokenBucket calculates new tokens: `min(capacity, old_tokens + elapsed * refill_rate)`
12. TokenBucket checks if new_tokens >= 1 → YES, subtract 1
13. TokenBucket calls `Storage.set(key, (tokens=4.0, last_refill=12:00:05))` atomically
14. TokenBucket returns `(allowed=True, remaining=4)`
15. Service returns `RateLimitResult(allowed=True, remaining=4, reset_in=0.1s)`
16. Middleware adds headers: `X-RateLimit-Limit: 10`, `X-RateLimit-Remaining: 4`, `X-RateLimit-Reset: <timestamp>`
17. Middleware calls `await call_next(request)` → route handler executes
18. Response returns through middleware stack to client with 200 status

**Reject Path (Rate Limit Exceeded):**

1. Steps 1-11 same as happy path
2. TokenBucket checks if new_tokens >= 1 → NO, new_tokens = 0.3
3. TokenBucket returns `(allowed=False, remaining=0)`
4. Service returns `RateLimitResult(allowed=False, remaining=0, reset_in=0.7s)`
5. Middleware adds headers: `X-RateLimit-Limit: 10`, `X-RateLimit-Remaining: 0`, `X-RateLimit-Reset: <timestamp>`, `Retry-After: 1`
6. Middleware raises `RateLimitExceeded` exception
7. Global exception handler in `main.py` catches exception
8. Handler returns `JSONResponse(status_code=429, content={"detail": "API rate limit exceeded"})`
9. Response returns to client with 429 status

**State Management:**
- Stateless per request (no session required)
- State stored in-memory: `dict[tuple[str, str], BucketState]` where key is (client_id, endpoint)
- State mutated only in TokenBucket.consume() with calculated refill
- No background jobs required — refill calculated on-demand per request
- State resets on application restart (acceptable for single instance deployment)

**Concurrency:**
- In-memory storage NOT thread-safe by default
- Must use `threading.Lock` for atomic get-calculate-set operations in TokenBucket
- Alternative: Use Redis with INCRBYFLOAT and EXPIRE for distributed deployment

## Architecture Patterns

### Pattern 1: Middleware-Based Interception

**What:** Insert rate limiting logic into FastAPI middleware stack, running before route handlers

**When:** You need to protect all (or most) API endpoints uniformly with minimal code changes

**Why it works:** 
- Separation of concerns: routing logic stays in handlers, rate limiting in middleware
- DRY principle: one middleware applies to all routes automatically
- Easy to enable/disable: add/remove from middleware list
- Access to request metadata (IP, path, method) before business logic executes

**Example:**
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.middleware.rate_limit.middleware import RateLimitMiddleware

app = FastAPI()

# Register middleware (runs in reverse order of registration)
app.add_middleware(RateLimitMiddleware)

# Exemptions handled inside middleware
@app.get("/health")
async def health_check():
    return {"status": "healthy"}  # Exempt, middleware skips

@app.post("/api/v1/prediction/predict")
async def predict():
    # Rate limited automatically by middleware
    return {"probability_up": 0.75}
```

### Pattern 2: Token Bucket with On-Demand Refill

**What:** Calculate token refill on each request based on elapsed time, no background jobs

**When:** You need accurate rate limiting without polling/background threads

**Why it works:**
- Eliminates need for scheduler/background tasks
- Scales to millions of buckets (only active buckets consume memory)
- Accurate to millisecond precision
- Simple implementation: `tokens = min(capacity, tokens + elapsed * refill_rate)`

**Algorithm:**
```python
def consume(client_id: str, endpoint: str, tokens_requested: int = 1) -> tuple[bool, int]:
    """
    Attempt to consume tokens from bucket, refilling based on elapsed time.
    
    Returns (allowed, tokens_remaining).
    """
    current_time = time.time()
    config = get_config(endpoint)
    
    # Retrieve current state
    state = storage.get((client_id, endpoint))
    if state is None:
        state = BucketState(tokens=config.capacity, last_refill=current_time)
    
    # Calculate refill
    elapsed = current_time - state.last_refill
    refilled_tokens = state.tokens + (elapsed * config.refill_rate)
    available_tokens = min(config.capacity, refilled_tokens)
    
    # Attempt consumption
    if available_tokens >= tokens_requested:
        new_tokens = available_tokens - tokens_requested
        storage.set((client_id, endpoint), BucketState(tokens=new_tokens, last_refill=current_time))
        return (True, int(new_tokens))
    else:
        # Denied, but update state with refilled tokens
        storage.set((client_id, endpoint), BucketState(tokens=available_tokens, last_refill=current_time))
        return (False, 0)
```

### Pattern 3: Storage Abstraction Layer

**What:** Define a generic storage interface, implement with in-memory dict (v1) and Redis (v2)

**When:** You need flexibility to swap storage backends without changing algorithm logic

**Why it works:**
- Testability: mock storage in unit tests
- Evolvability: start with in-memory, migrate to Redis later
- Separation: TokenBucket doesn't care about storage implementation

**Interface:**
```python
from abc import ABC, abstractmethod
from typing import Optional

class RateLimitStorage(ABC):
    """Abstract interface for rate limit state storage."""
    
    @abstractmethod
    def get(self, key: tuple[str, str]) -> Optional[BucketState]:
        """Retrieve bucket state for (client_id, endpoint)."""
        pass
    
    @abstractmethod
    def set(self, key: tuple[str, str], state: BucketState) -> None:
        """Store bucket state atomically."""
        pass

class InMemoryStorage(RateLimitStorage):
    """Single-instance in-memory storage with thread safety."""
    
    def __init__(self):
        self._state: dict[tuple[str, str], BucketState] = {}
        self._lock = threading.Lock()
    
    def get(self, key: tuple[str, str]) -> Optional[BucketState]:
        with self._lock:
            return self._state.get(key)
    
    def set(self, key: tuple[str, str], state: BucketState) -> None:
        with self._lock:
            self._state[key] = state

class RedisStorage(RateLimitStorage):
    """Distributed Redis-backed storage (future enhancement)."""
    
    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url)
    
    def get(self, key: tuple[str, str]) -> Optional[BucketState]:
        data = self._redis.get(self._serialize_key(key))
        return self._deserialize(data) if data else None
    
    def set(self, key: tuple[str, str], state: BucketState) -> None:
        self._redis.set(
            self._serialize_key(key),
            self._serialize(state),
            ex=3600  # Expire after 1 hour of inactivity
        )
```

### Pattern 4: Per-Endpoint Configuration with Fallback

**What:** Define rate limits per endpoint, falling back to global default

**When:** You need strict limits on expensive endpoints (e.g., ML prediction) and lenient limits on read-only endpoints

**Why it works:**
- Flexibility: different endpoints have different cost profiles
- Safety: global default prevents unconfigured endpoints from being unprotected
- Simplicity: configuration via environment variables

**Configuration:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Global defaults
    RATE_LIMIT_DEFAULT_REQUESTS: int = 100
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_DEFAULT_BURST: int = 20
    
    # Per-endpoint overrides (format: "METHOD:path=rate,window,burst")
    RATE_LIMIT_OVERRIDES: dict[str, str] = {
        "POST:/api/v1/prediction/predict": "10,60,5",  # 10 req/min, burst 5
        "GET:/api/v1/historic-data/live": "60,60,20",  # 60 req/min, burst 20
    }
    
    # Exemptions (no rate limit)
    RATE_LIMIT_EXEMPT_PATHS: list[str] = ["/health", "/docs", "/openapi.json", "/redoc"]
    
    class Config:
        env_file = ".env"

def get_rate_limit_config(endpoint: str) -> RateLimitConfig:
    """Retrieve rate limit config for endpoint, falling back to default."""
    settings = get_settings()
    
    if endpoint in settings.RATE_LIMIT_EXEMPT_PATHS:
        return RateLimitConfig(rate=float('inf'), burst=float('inf'))  # Unlimited
    
    override = settings.RATE_LIMIT_OVERRIDES.get(endpoint)
    if override:
        rate, window, burst = map(int, override.split(','))
        return RateLimitConfig(rate=rate, window=window, burst=burst)
    
    # Fallback to default
    return RateLimitConfig(
        rate=settings.RATE_LIMIT_DEFAULT_REQUESTS,
        window=settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS,
        burst=settings.RATE_LIMIT_DEFAULT_BURST
    )
```

### Pattern 5: Response Header Enrichment

**What:** Add standard HTTP headers to responses indicating rate limit status

**When:** Always — this is best practice for API clients

**Why it works:**
- Transparency: clients know their limits without hitting 429
- Client-side retry logic: `Retry-After` header tells clients when to retry
- Debugging: developers can see remaining quota in HTTP response

**Headers (following GitHub/Stripe conventions):**
- `X-RateLimit-Limit: <capacity>` — Maximum requests per window
- `X-RateLimit-Remaining: <remaining>` — Requests remaining in current window
- `X-RateLimit-Reset: <timestamp>` — Unix timestamp when bucket fully refills
- `Retry-After: <seconds>` — (Only on 429) Seconds to wait before retrying

**Implementation:**
```python
async def __call__(self, request: Request, call_next) -> Response:
    # ... rate limit check ...
    
    # Enrich response with headers
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(config.capacity)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(int(result.reset_time))
    
    if not result.allowed:
        response.headers["Retry-After"] = str(int(result.reset_in))
    
    return response
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Leaky Bucket with Queue

**What:** Implementing a literal queue that drains at a fixed rate

**Why bad:**
- Memory overhead: queue stores every request, unbounded growth under attack
- Latency: requests wait in queue, degrading user experience
- Complexity: requires background worker to drain queue
- Starvation: old requests block new requests

**Instead:** Use token bucket with on-demand refill (Pattern 2) — same smoothing effect, no queue overhead

### Anti-Pattern 2: Fixed Window without Burst Handling

**What:** Reset counter at fixed intervals (e.g., top of every minute)

**Why bad:**
- Boundary problem: 200 requests at 12:00:59, 200 requests at 12:01:00 = 400 requests in 2 seconds
- Stampede effect: all clients retry at top of hour when limit resets
- No burst accommodation: legitimate spikes get rejected

**Instead:** Use sliding window or token bucket (both handle bursts gracefully)

### Anti-Pattern 3: Per-Request Database Lookup for State

**What:** Hitting PostgreSQL/Redis on every request to read/update counters

**Why bad:**
- Latency: 5-50ms per request just for rate limit check
- Database load: rate limiting becomes bottleneck
- Race conditions: get-then-set pattern allows concurrent requests to bypass limit

**Instead:** Use in-memory storage with atomic operations (Pattern 3), sync to database periodically if multi-instance needed

### Anti-Pattern 4: Rate Limiting in Route Handlers

**What:** Manually calling rate limiter in each route function

**Why bad:**
- Not DRY: copy-paste logic across routes
- Easy to forget: new endpoints unprotected
- Mixed concerns: business logic cluttered with infrastructure code

**Instead:** Use middleware pattern (Pattern 1) — automatic protection for all routes

### Anti-Pattern 5: Ignoring X-Forwarded-For Header

**What:** Rate limiting by `request.client.host` only

**Why bad:**
- Proxy problem: all requests appear from proxy IP, single bucket for all clients
- Shared limit: everyone behind corporate proxy shares one quota
- Bypass: attacker can rotate proxies to evade limit

**Instead:** Trust `X-Forwarded-For` if behind known proxy, with validation:
```python
def get_client_id(request: Request) -> str:
    """Extract client IP, trusting X-Forwarded-For from known proxies."""
    if request.client.host in TRUSTED_PROXIES:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP (original client)
            return forwarded.split(",")[0].strip()
    return request.client.host
```

## Scalability Considerations

| Scale | Architecture | Storage | Notes |
|-------|--------------|---------|-------|
| **< 100 req/sec** | Single FastAPI instance, in-memory storage | `dict[tuple, BucketState]` with `threading.Lock` | Sufficient for MVP and small deployments |
| **100-10K req/sec** | Single instance, Redis storage | Redis with `INCRBYFLOAT` + `EXPIRE` | Redis adds <1ms latency, handles crashes |
| **10K-100K req/sec** | Multi-instance, Redis Cluster | Redis Cluster with sharding by client_id | Horizontal scaling, consistent hashing |
| **> 100K req/sec** | Multi-instance, eventually consistent | Redis + local cache with periodic sync | Trade consistency for performance (Stripe pattern) |

**Concurrency in Single Instance:**
- Python GIL limits true parallelism
- Use `threading.Lock` for atomic get-update-set in token bucket
- Lock contention becomes bottleneck at ~1K req/sec
- Solution: Shard buckets across multiple dicts with separate locks

**Distributed Rate Limiting:**
If deploying multiple FastAPI instances (e.g., Kubernetes with 3 replicas), you need centralized state:

1. **Redis with Lua script** (atomic operations):
   ```lua
   -- Token bucket refill and consume (atomic)
   local key = KEYS[1]
   local capacity = tonumber(ARGV[1])
   local refill_rate = tonumber(ARGV[2])
   local tokens_requested = tonumber(ARGV[3])
   local current_time = tonumber(ARGV[4])
   
   local state = redis.call('HMGET', key, 'tokens', 'last_refill')
   local tokens = tonumber(state[1]) or capacity
   local last_refill = tonumber(state[2]) or current_time
   
   local elapsed = current_time - last_refill
   local refilled = math.min(capacity, tokens + (elapsed * refill_rate))
   
   if refilled >= tokens_requested then
       redis.call('HMSET', key, 'tokens', refilled - tokens_requested, 'last_refill', current_time)
       redis.call('EXPIRE', key, 3600)  -- Expire after 1 hour
       return {1, math.floor(refilled - tokens_requested)}
   else
       redis.call('HMSET', key, 'tokens', refilled, 'last_refill', current_time)
       return {0, 0}
   end
   ```

2. **Eventually consistent pattern** (Stripe approach):
   - Each instance maintains in-memory counter
   - Periodically sync to Redis (e.g., every 10 seconds)
   - On sync: push local counter increment, pull global count
   - Trade-off: May exceed limit by N * sync_interval during burst (acceptable for most cases)

## Build Order (Dependency Graph)

The components should be built in this order to minimize rework:

```
Phase 1: Foundation (No dependencies)
├─ Storage abstraction interface (RateLimitStorage ABC)
├─ Configuration schema (RateLimitConfig Pydantic model)
└─ Domain exceptions (RateLimitExceeded)

Phase 2: Algorithm Core (Depends on Phase 1)
├─ BucketState data class
├─ InMemoryStorage implementation
└─ TokenBucket class (uses Storage, Config)

Phase 3: Service Layer (Depends on Phase 2)
└─ RateLimiterService (orchestrates TokenBucket + Config)

Phase 4: Integration (Depends on Phase 3)
├─ RateLimitMiddleware (uses Service)
└─ Global exception handler for RateLimitExceeded

Phase 5: Configuration (Depends on Phase 4)
├─ Settings class with per-endpoint overrides
└─ Dependency injection for service
```

**Rationale:**
- Storage abstraction first → enables easy testing with mock storage
- Algorithm before service → core logic isolated from FastAPI concerns
- Middleware last → requires working service to integrate
- Configuration throughout → start with hardcoded defaults, make configurable incrementally

**Suggested first commit:**
```python
# Phase 1 minimal viable code
from abc import ABC, abstractmethod
from typing import Optional, NamedTuple

class BucketState(NamedTuple):
    tokens: float
    last_refill: float

class RateLimitStorage(ABC):
    @abstractmethod
    def get(self, key: tuple[str, str]) -> Optional[BucketState]:
        pass
    
    @abstractmethod
    def set(self, key: tuple[str, str], state: BucketState) -> None:
        pass

# Now you can write tests against this interface before implementing TokenBucket
```

## Sources

**HIGH confidence sources:**
- [Nginx Rate Limiting](https://blog.nginx.org/blog/rate-limiting-nginx) — Industry-standard implementation, explains leaky bucket vs token bucket (2017, but patterns still current)
- [Stripe: Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters) — Production architecture from major API provider, sliding window pattern (2017)
- [AWS: Rate Limiting Strategies for Serverless Applications](https://aws.amazon.com/blogs/architecture/rate-limiting-strategies-for-serverless-applications/) — Serverless patterns, distributed system considerations (2021)

**MEDIUM confidence sources:**
- [Kong: How to Design a Scalable Rate Limiting Algorithm](https://konghq.com/blog/engineering/how-to-design-a-scalable-rate-limiting-algorithm) — Implementation details, algorithm comparisons (2021)

**Implementation references (HIGH confidence):**
- FastAPI middleware documentation: https://fastapi.tiangolo.com/tutorial/middleware/
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Python threading.Lock: https://docs.python.org/3/library/threading.html#lock-objects

**Note on token bucket algorithm:**
All sources (Nginx, Stripe, AWS, Kong) converge on token bucket or sliding window as the recommended algorithms. Fixed window and leaky bucket are mentioned primarily as historical context or anti-patterns. Token bucket is explicitly used by AWS Lambda, Stripe API, GitHub API, and Google Cloud APIs — this is the industry standard for 2020s.

**Confidence assessment:** HIGH — Core patterns verified across multiple production systems (Stripe, AWS, Nginx, Kong). Token bucket algorithm is well-documented with 40+ years of research. FastAPI middleware integration is straightforward (official docs + community examples). The main uncertainty is around distributed rate limiting (Redis Lua scripts), but since PROJECT.md scopes this to single instance, in-memory storage is HIGH confidence.
