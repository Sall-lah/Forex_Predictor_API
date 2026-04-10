# Stack Research

**Domain:** Reliable production forex prediction API (brownfield FastAPI ML service)
**Researched:** 2026-04-11
**Confidence:** HIGH

## Recommended Stack (2025 production standard)

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | 3.12.x | Runtime | Already in-repo; stable for FastAPI + scientific stack (NumPy/Pandas/LightGBM) with mature ecosystem support. | HIGH |
| FastAPI | 0.135.3 | API framework | Keep existing framework; production-ready ASGI stack, strong typing, and official production guidance with multi-worker deployment + lifespan resource management. | HIGH |
| Uvicorn | 0.44.0 | ASGI server | Officially recommended server for FastAPI; supports multi-process workers for throughput and fault isolation. | HIGH |
| Pydantic | 2.12.5 | Runtime validation/contracts | Strong request/response schema guarantees; reduces bad-input and contract-drift incidents in production. | HIGH |
| Pydantic Settings | 2.13.1 | Environment config + secrets loading | Standard way to centralize config and secrets source precedence (env/.env/secrets manager), critical for predictable prod behavior. | HIGH |

### Reliability & Operations Additions (for this milestone)

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| httpx | 0.28.1 | External HTTP client (Kraken calls) | Keep for market-data calls, but enforce strict timeout/connect/read limits per request. | HIGH |
| tenacity | 9.1.4 | Retry with bounded exponential backoff + jitter | Wrap transient upstream failures (Kraken/network) only; never retry validation bugs or deterministic model errors. | HIGH |
| redis | 7.4.0 | Shared operational state (rate-limit counters, response cache, idempotency keys) | Add when running multiple API replicas; required for horizontally consistent rate limiting/caching. | HIGH |
| prometheus-client | 0.25.0 | Metrics exposition (`/metrics`) | Use for RED/USE metrics and SLO alerting; supports multiprocess collection patterns. | HIGH |
| opentelemetry-sdk | 1.41.0 | Distributed traces/metrics SDK | Use for end-to-end traceability across ingress → Kraken call → feature pipeline → model inference. | HIGH |
| opentelemetry-instrumentation-fastapi | 0.62b0 | Auto-instrument FastAPI spans | Add for low-friction baseline tracing; supplement with manual spans around model and feature steps. | HIGH |
| opentelemetry-exporter-otlp | 1.41.0 | Telemetry export to collector | Use OTLP to avoid vendor lock-in and route data to Prometheus/Grafana/Datadog/etc via collector. | HIGH |
| sentry-sdk | 2.57.0 | Exception and performance error monitoring | Add if you want high-signal production incident triage with filtering/sampling controls. | HIGH |

### Model Quality & Validation Toolchain

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| mlflow | 3.11.1 | Experiment tracking + model registry + evaluation artifacts | Use to gate model promotion with reproducible metrics and alias-based deployment (`champion`/`challenger`), not deprecated stages. | HIGH |
| evidently | 0.7.21 | Drift/performance monitoring reports | Use for post-deploy monitoring on feature drift, target drift (when labels arrive), and prediction quality trends. | MEDIUM |
| pandera | 0.30.1 | Dataframe schema validation for features | Use before inference to fail fast on feature shape/type drift that would silently degrade model quality. | MEDIUM |

### Test & Release Hardening Tools

| Tool | Version | Purpose | Notes | Confidence |
|------|---------|---------|-------|------------|
| pytest | 9.0.3 | Core test framework | Keep as base for unit/integration suites. | HIGH |
| pytest-asyncio | 1.3.0 | Async endpoint/service tests | Required for robust async FastAPI + external I/O behavior tests. | HIGH |
| pytest-xdist | 3.8.0 | Parallel test execution | Use in CI to keep hardening suite fast enough for PR gating. | HIGH |
| schemathesis | 4.15.1 | OpenAPI contract fuzz/property testing | Use against `/openapi.json` to catch edge-case contract failures before production. | HIGH |
| hypothesis | 6.151.12 | Property-based testing | Use for feature engineering and probability-output invariants. | HIGH |
| locust | 2.43.4 | Load and soak testing | Use before releases to validate tail latency and failure behavior under realistic throughput. | MEDIUM |
| ruff | 0.15.10 | Linting/format quality gate | Use as fast CI gate to reduce low-level defects and style drift. | MEDIUM |
| mypy | 1.20.0 | Static type checks | Important for catching model pipeline contract mismatches pre-runtime. | MEDIUM |

### Deployment Baseline

| Component | Version | Purpose | Why |
|-----------|---------|---------|-----|
| gunicorn | 25.3.0 | Process manager for Uvicorn workers (Linux containers) | Operationally mature worker supervision and graceful restarts for production containers. |
| Kubernetes probes | v1.32 docs pattern | `startupProbe` + `readinessProbe` + `livenessProbe` | Prevents routing traffic before model warm-up and detects deadlocks without restart flapping. |

## Installation (pip)

```bash
# Reliability + observability
pip install tenacity redis prometheus-client sentry-sdk
pip install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi

# Model quality + validation
pip install mlflow evidently pandera

# Test and release hardening
pip install -D pytest pytest-asyncio pytest-xdist schemathesis hypothesis locust ruff mypy
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| OpenTelemetry + OTLP | Vendor-specific-only APM SDK as primary | If org is permanently committed to one observability vendor and wants minimal setup. |
| MLflow Registry aliases | Hand-rolled model version folders / manual artifact naming | Only for tiny single-model projects with no promotion workflow or audit requirements. |
| Schemathesis + pytest | Pure hand-written endpoint tests | Only if API surface is very small and schema evolves rarely. |
| Redis shared state | In-memory per-process cache/rate limit state | Only for single-instance deployments (not production-scale). |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| MLflow model **stages** as the primary promotion mechanism | MLflow docs mark stages deprecated; this creates migration debt. | Model aliases (`champion`, `challenger`, environment aliases) + tags. |
| Unbounded retries on upstream data fetches | Can amplify outages and exhaust worker pools; harms latency SLOs. | Tenacity with capped attempts + exponential backoff + jitter + circuit-breaker semantics. |
| Single-process production serving | One process is fragile under CPU spikes and cannot exploit multicore for concurrent API traffic. | Multi-worker Uvicorn/Gunicorn deployment with health probes. |
| “Metrics only” observability | Metrics alone miss causality for intermittent upstream/model latency incidents. | Metrics + traces (+ error events) using OTel + Prometheus + Sentry. |
| Silent schema coercion for model inputs | Hidden data drift lowers model quality before alarms fire. | Explicit feature contracts via Pandera + fail-fast request rejection. |

## Stack Patterns by Deployment Variant

**If single-region, moderate traffic (<10k req/min):**
- FastAPI + Uvicorn workers, Redis, Prometheus, OTel collector, MLflow
- Because this gives reliable SLO observability and safe model promotion without over-engineering.

**If multi-region / high availability target:**
- Add active-active API replicas, regional Redis strategy, per-region telemetry pipelines, canary model alias rollout
- Because failure isolation and staged rollout become more important than raw model throughput.

## Version Compatibility Notes

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastAPI 0.135.3 | Pydantic 2.12.5 | Current FastAPI line is Pydantic v2-native. |
| opentelemetry-sdk 1.41.0 | opentelemetry-instrumentation-fastapi 0.62b0 | Keep API/SDK and instrumentation packages aligned by release family. |
| redis 7.4.0 | tenacity 9.1.4 | Combine Redis connectivity + bounded retries for resilient cache/state operations. |
| pytest 9.0.3 | pytest-asyncio 1.3.0 + pytest-xdist 3.8.0 | Standard modern async + parallel CI test stack. |

## Sources

- Context7 `/fastapi/fastapi/0.128.0` — production workers + lifespan recommendations (HIGH)
- Context7 `/pydantic/pydantic-settings` — settings source precedence + secrets loading (HIGH)
- Context7 `/open-telemetry/opentelemetry-python` — OTLP exporter and production instrumentation guidance (HIGH)
- Context7 `/prometheus/client_python` — FastAPI/ASGI metrics and multiprocess patterns (HIGH)
- Context7 `/mlflow/mlflow/v3.1.4` — model aliases and stage deprecation guidance (HIGH)
- Context7 `/evidentlyai/evidently` — drift monitoring/report workflow (MEDIUM)
- Context7 `/jd/tenacity` — bounded retries, backoff, jitter patterns (HIGH)
- Context7 `/redis/redis-py/v6_4_0` — retry + health-check client patterns (HIGH)
- Context7 `/schemathesis/schemathesis` — OpenAPI fuzz/stateful testing with pytest (HIGH)
- Context7 `/getsentry/sentry-python` — FastAPI monitoring, filtering, sampling (HIGH)
- Context7 `/websites/kubernetes_io` — startup/readiness/liveness probe patterns (HIGH)
- Official PyPI JSON endpoints (package metadata) for listed versions, queried 2026-04-11 (MEDIUM)

---
*Stack research for: forex prediction API reliability hardening & production readiness*
*Researched: 2026-04-11*
