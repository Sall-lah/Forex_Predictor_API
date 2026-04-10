# Architecture Research

**Domain:** Production forex prediction API (brownfield FastAPI monolith)
**Researched:** 2026-04-11
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│                         Edge & API Control Layer                             │
├───────────────────────────────────────────────────────────────────────────────┤
│  LB/Ingress  →  FastAPI App                                                  │
│                 ├─ Request ID + structured logging middleware                │
│                 ├─ Rate-limit middleware (Redis-backed)                      │
│                 ├─ AuthN/Z middleware (future)                               │
│                 └─ Exception translation (domain error → HTTP contract)      │
├───────────────────────────────────────────────────────────────────────────────┤
│                           Application/Domain Layer                            │
├───────────────────────────────────────────────────────────────────────────────┤
│  HistoricDataService         PredictionService                               │
│  ValidationService           Health/Readiness Service                        │
│  ReliabilityPolicyService (timeouts/retries/circuit state)                  │
├───────────────────────────────────────────────────────────────────────────────┤
│                             Adapter/Integration Layer                         │
├───────────────────────────────────────────────────────────────────────────────┤
│  MarketDataAdapter (Kraken)   ModelRuntimeAdapter (LightGBM artifact)        │
│  TelemetryAdapter (OpenTelemetry)   CacheAdapter (Redis)                     │
│  PersistenceAdapter (Postgres/object store for audit + validation outputs)   │
├───────────────────────────────────────────────────────────────────────────────┤
│                           Data, Ops, and Offline Validation                   │
├───────────────────────────────────────────────────────────────────────────────┤
│  Redis (rate limit + hot cache)   Postgres (request/prediction audit)        │
│  Object storage/model registry     Metrics/Trace backend (OTLP target)       │
│  Scheduled validation jobs (backtest, drift, calibration checks)             │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| API Router Layer | Endpoint composition and dependency injection only | `APIRouter` modules per feature, no business logic |
| Domain Services | Prediction/data workflows, domain validation, policy enforcement | Plain Python services raising domain exceptions |
| Market Data Adapter | Kraken API call envelope handling, retry/timeout policy, normalization | Reused `httpx.Client`/`AsyncClient` with explicit `Timeout`/`Limits` |
| Model Runtime Adapter | Safe model loading, feature alignment contract, inference guardrails | Thread-safe singleton + startup warmup via lifespan |
| Validation Subsystem | Input/output/model-contract checks + ongoing quality checks | Runtime validators + async validation jobs |
| Operational Controls | Rate limiting, readiness, observability, configuration scope | Middleware + OTel + health/readiness endpoints |

## Recommended Project Structure

```text
app/
├── api/                         # Router aggregation only
├── core/                        # Settings, exception hierarchy, lifespan bootstrap
├── middleware/                  # Cross-cutting controls (rate limit, request-id, auth)
├── features/
│   ├── historic_data/
│   │   ├── router.py            # HTTP contract
│   │   ├── service.py           # Use-case orchestration
│   │   └── schemas.py           # DTOs
│   ├── prediction/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── validators.py        # Feature/output contract checks
│   │   └── schemas.py
│   └── validation/              # New: offline/online validation endpoints + jobs trigger
├── adapters/
│   ├── market_data/             # Kraken adapter + retries/circuit policy
│   ├── model_runtime/           # Artifact loading/version metadata
│   ├── cache/                   # Redis adapters
│   └── telemetry/               # OpenTelemetry setup
├── repositories/                # Audit/event persistence boundaries
└── workers/                     # Scheduled backtesting/drift/calibration tasks
```

### Structure Rationale

- **Keep layered monolith:** right choice for current stage; add strict boundaries before microservices.
- **Adapters as explicit boundary:** prevents Kraken/model/Redis details leaking into feature services.
- **Validation as first-class module:** avoids treating quality checks as ad-hoc test scripts.

## Architectural Patterns

### Pattern 1: Lifespan-managed startup for critical dependencies

**What:** Load/warm critical resources (model, Redis, telemetry) at startup and expose readiness based on successful initialization.
**When to use:** Always in production; especially where inference depends on local artifacts.
**Trade-offs:** Slightly longer startup; much safer runtime behavior.

**Example:**
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model_or_fail()
    app.state.http_client = build_http_client()
    yield
    app.state.http_client.close()

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: Ports-and-adapters around external dependencies

**What:** Domain services call abstract adapter interfaces; adapters own retries/timeouts/transport details.
**When to use:** For Kraken, model registry, Redis, telemetry exporters.
**Trade-offs:** More files/abstractions; major gain in testability and swap safety.

### Pattern 3: Split synchronous serving path from asynchronous validation path

**What:** Keep `/predict` request path lean; run heavier validation (replay, drift, calibration, backtests) in scheduled/background workers.
**When to use:** Required once operational confidence is a project goal.
**Trade-offs:** Additional infrastructure; avoids p95/p99 latency spikes.

## Data Flow

### Request Flow (prediction)

```text
Client
  ↓
Ingress/LB
  ↓
FastAPI middleware stack (request-id → rate limit → auth → exception map)
  ↓
Prediction router (schema validation)
  ↓
PredictionService
  ├─→ MarketDataAdapter (Kraken OHLC fetch)
  ├─→ Feature extraction + contract checks
  ├─→ ModelRuntimeAdapter (predict_proba)
  ├─→ Output validator (probability sanity/calibration guardrails)
  └─→ Audit repository write (request, features hash, model version, response)
  ↓
API response + rate-limit headers + trace context
```

### Operational/Validation Flow (async)

```text
Scheduler/cron
  ↓
Validation worker
  ├─→ Pull recent predictions + realized prices
  ├─→ Compute directional accuracy, calibration, drift
  ├─→ Persist validation metrics/history
  ├─→ Emit telemetry + alerts on threshold breach
  └─→ Optionally set model/route readiness flag to degraded
```

### Key Data Flows

1. **Serving flow (online):** Request → prediction in < strict timeout budget; failures are explicit (422/502/503), never silent fallback.
2. **Trust flow (offline):** Predictions + realized outcomes → rolling validation metrics → operational decisions (alerts, degraded mode, rollback trigger).

## Component Boundaries (for roadmap planning)

| Boundary | Owns | Must NOT own |
|----------|------|--------------|
| `features/*/router.py` | HTTP contract, dependency wiring | Kraken calls, model logic, retries |
| `features/*/service.py` | Use-case orchestration and domain rules | HTTP status codes, transport-level details |
| `adapters/market_data` | HTTPX client reuse, timeout/limit/retry policy, envelope parse | Feature engineering, response DTO shaping |
| `adapters/model_runtime` | Model loading/versioning/inference contract | Request parsing, external API calls |
| `workers/validation` | Backtest/drift/calibration computations | Live request serving |
| `middleware/*` | Cross-cutting controls (rate-limit, request-id, auth) | Domain prediction decisions |

## Suggested Build Order (subsequent milestone)

1. **Harden serving path reliability first**
   - Introduce lifespan startup/readiness separation (model + dependencies).
   - Switch Kraken access to reusable HTTPX client with explicit timeout/limits and controlled retries.
   - Add circuit-break/degraded-mode state for upstream data failures.
   - *Why first:* prevents frequent incidents before adding more capabilities.

2. **Operational controls second**
   - Upgrade rate-limit storage from in-memory to Redis for multi-instance correctness.
   - Add request IDs, structured logs, OpenTelemetry tracing/metrics.
   - Add `/ready` endpoint with dependency checks (not just `/health`).
   - *Why second:* once behavior is stable, make it observable and operable.

3. **Validation capabilities third**
   - Add prediction audit persistence (model version + features fingerprint + output).
   - Add scheduled validation worker (accuracy, calibration, drift) and thresholds.
   - Wire alerting/degraded toggles from validation outcomes.
   - *Why third:* depends on observability and reliable data capture from prior steps.

4. **Scale refinements last**
   - Add caching strategy for repeat pair/timeframe requests.
   - Optimize feature computation hot paths and concurrency limits.
   - Consider service split only after clear saturation signals.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k active users | Single FastAPI deployment, layered monolith, Redis for rate limit/cache, strict timeout budgets |
| 1k-100k | Multiple app replicas, centralized Redis + Postgres, full OTel dashboards + SLO alerting |
| 100k+ | Separate prediction-serving and validation workers, potentially split market-data adapter into dedicated service |

## Anti-Patterns

### Anti-Pattern 1: “All logic in router/service blob”

**What people do:** Mix HTTP handling, Kraken transport logic, feature engineering, and model loading in one module.
**Why it’s wrong:** Reliability changes become risky and untestable; incident triage is slow.
**Do this instead:** Keep strict boundaries: router → domain service → adapters.

### Anti-Pattern 2: In-memory controls in multi-instance production

**What people do:** Keep rate limits/audit state only in process memory.
**Why it’s wrong:** Limits become inconsistent across replicas; operational trust degrades.
**Do this instead:** Use Redis/Postgres for shared state and deterministic behavior.

### Anti-Pattern 3: No explicit model/data contract versioning

**What people do:** Load model artifact and hope feature columns still match.
**Why it’s wrong:** Silent prediction degradation or hard runtime failures.
**Do this instead:** Enforce feature schema contract + model version metadata at startup and per request.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Kraken Spot REST (OHLC) | Adapter with reusable HTTPX client, explicit timeouts/limits/retries | Handle upstream error envelope and throttling explicitly |
| OTLP collector/observability backend | OpenTelemetry SDK export (trace/metrics/logs) | Ensure correlation IDs in logs and traces |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Router ↔ Service | Direct dependency injection | Service raises domain exceptions only |
| Service ↔ Adapters | Interface-based direct calls | Adapter-level resilience policies centralized |
| API runtime ↔ Validation workers | DB/queue/event store | Async flow must not block request path |

## Sources

- FastAPI docs (larger apps with `APIRouter`): https://fastapi.tiangolo.com/tutorial/bigger-applications/ (HIGH)
- FastAPI docs/release notes (lifespan startup/shutdown pattern): https://fastapi.tiangolo.com/advanced/events/ and release notes examples (HIGH)
- FastAPI docs (middleware order behavior): https://fastapi.tiangolo.com/tutorial/middleware/ (HIGH)
- HTTPX docs (client reuse, resource limits, timeout tuning, transport retries): https://www.python-httpx.org/advanced/ (HIGH)
- OpenTelemetry Python docs (SDK/exporters/instrumentation patterns): https://opentelemetry.io/docs/languages/python/ (HIGH)
- Kraken API docs (REST limits and error behaviors): https://docs.kraken.com/api/docs/guides/spot-rest-ratelimits (MEDIUM — docs sections vary by product area; validate exact tier behavior for your account)
- Current project architecture baseline: `.planning/PROJECT.md` + `app/*` module structure (HIGH)

---
*Architecture research for: Forex prediction API reliability hardening milestone*
*Researched: 2026-04-11*
