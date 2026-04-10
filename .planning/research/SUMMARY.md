# Project Research Summary

**Project:** Forex Predictor API
**Domain:** Production-grade forex prediction API (FastAPI + ML inference)
**Researched:** 2026-04-11
**Confidence:** HIGH

## Executive Summary

This project is a reliability-first ML API, not a model-experiment sandbox. The combined research is consistent: expert teams ship this kind of product as a **layered FastAPI monolith** with strict contracts, dependency-aware readiness, bounded upstream failure handling, and strong observability. The immediate goal should be predictable online inference behavior under real outage and load conditions, then progressive addition of model quality governance.

The recommended approach is to keep the current Python/FastAPI base, harden the serving path first (timeouts/retries/circuit-breaker, committed-candle correctness, startup/readiness guarantees), then add shared operational controls (Redis-backed limits/state, tracing/metrics/logging), and only then expand into validation/drift/challenger workflows. This ordering matches both architecture dependencies and feature dependencies.

Key risk is silent trust erosion: incorrect market-data semantics (incomplete candles, limited OHLC backfill), hidden model/feature contract drift, and “healthy infra but degraded model quality.” Mitigation is explicit contracts everywhere: data freshness/completeness metadata in responses, artifact + feature schema version checks, persisted prediction audit trails, and delayed-label quality monitoring with alert thresholds.

## Key Findings

### Recommended Stack

The stack research strongly supports staying on the existing Python 3.12 + FastAPI path and adding production hardening components rather than re-platforming. Core emphasis is contract safety (Pydantic v2), resilient external I/O (httpx + tenacity), shared state for multi-instance correctness (Redis), and first-class observability (Prometheus + OpenTelemetry + optional Sentry).

**Core technologies:**
- **Python 3.12.x**: runtime baseline — stable compatibility across FastAPI + scientific ML ecosystem.
- **FastAPI 0.135.3 + Uvicorn 0.44.0 (+ Gunicorn 25.3.0 in containers)**: API serving — mature multi-worker production pattern.
- **Pydantic 2.12.5 + Pydantic Settings 2.13.1**: schema/config contracts — fail fast on bad inputs and config drift.
- **httpx 0.28.1 + tenacity 9.1.4**: upstream resilience — bounded timeout/retry/jitter for Kraken calls.
- **redis 7.4.0**: distributed limiter/cache/idempotency state for horizontal scale correctness.
- **prometheus-client 0.25.0 + OTel SDK/exporter/instrumentation 1.41.0/0.62b0**: metrics/tracing for SLO operations.
- **mlflow 3.11.1**: model registry/promotion with aliases (avoid deprecated stages).

### Expected Features

Feature research is clear on launch scope: reliability and contract guarantees are P1, while trust-enhancing model lifecycle features are P2/P3.

**Must have (table stakes):**
- Deterministic, versioned prediction API contract with model/data freshness metadata.
- Health vs readiness split with dependency-aware readiness checks.
- Stable error taxonomy + retry-safe HTTP semantics.
- Upstream timeout/retry/circuit-breaker behavior.
- Core observability (latency/error/request metrics, request IDs, structured logs).
- Rate limiting with quota visibility headers.

**Should have (competitive):**
- Champion/challenger (shadow predictions) for safe model rollout.
- Online drift + quality monitoring and alerting.
- SLO status reporting.

**Defer (v2+):**
- Backtest/replay public API.
- Explainability payloads on response path.

### Architecture Approach

Architecture should remain a **layered monolith with strict boundaries**: routers for HTTP wiring only, domain services for orchestration/policy, adapters for Kraken/model/Redis/telemetry integration details, and separate async workers for heavy validation. Lifespan-managed startup for model/client initialization and dependency-aware readiness is non-negotiable. Keep online inference path lean; move drift/backtest/calibration to asynchronous jobs.

**Major components:**
1. **Edge/API control layer** — middleware for request IDs, rate limiting, auth (future), exception translation.
2. **Domain services layer** — prediction workflow, validation policies, health/readiness logic.
3. **Adapter/integration layer** — Kraken client, model runtime, telemetry, cache/persistence boundaries.
4. **Async validation/ops layer** — scheduled quality checks, drift/calibration, degraded-mode signaling.

### Critical Pitfalls

1. **Incomplete-candle leakage from Kraken OHLC** — exclude current uncommitted candle and test for it explicitly.
2. **Assuming deep OHLC backfill exists** — Kraken OHLC is bounded; persist your own historical snapshots.
3. **Retry storms during upstream incidents** — use capped retries, jitter, circuit-breakers, and strict timeout budgets.
4. **Process-local limiter state at scale** — move quota/limit state to Redis and key by authenticated principal.
5. **Model/feature contract drift** — pin dependency matrix, store artifact manifest, and enforce feature schema/version checks at startup and inference.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Data & Serving Reliability Hardening
**Rationale:** Every later feature depends on correct and stable live-data ingestion + predictable request behavior.
**Delivers:** Committed-candle handling, OHLC gap/completeness checks, reusable HTTPX client with bounded timeout/retry policy, circuit-breaker/degraded strategy, deterministic prediction schema and error taxonomy.
**Addresses:** P1 contract + upstream resilience features.
**Avoids:** Pitfalls 1, 2, and 3.

### Phase 2: Operational Controls & API Governance
**Rationale:** Once serving path is reliable, enforce global traffic/control behavior and production operability.
**Delivers:** Redis-backed distributed rate limiting, principal-based auth/quota keys, readiness endpoint with dependency checks, request IDs + structured logs + core metrics/traces.
**Uses:** Redis, Prometheus, OTel, Pydantic Settings.
**Implements:** Middleware + operational service boundaries from architecture research.
**Avoids:** Pitfalls 4 and 9.

### Phase 3: Model Contract & Release Governance
**Rationale:** Reliability without model governance still leaves silent quality regressions.
**Delivers:** Artifact manifest/version compatibility gates, feature schema contract validation, prediction audit persistence (model version + feature fingerprint), MLflow alias-based promotion workflow, shadow/challenger plumbing.
**Addresses:** P2 safe rollout prerequisite.
**Avoids:** Pitfalls 5 and 6.

### Phase 4: Continuous Quality Evaluation & Trust Signals
**Rationale:** After instrumentation and audit storage exist, evaluate real-world quality and expose trust metadata.
**Delivers:** Scheduled drift/calibration/accuracy jobs, threshold alerts, SLO status reporting, response-level degraded/freshness/completeness signals.
**Addresses:** P2 drift monitoring + trust reporting.
**Avoids:** Pitfalls 7, 8, and 10.

### Phase 5: Advanced Product Surface (v2+)
**Rationale:** Only pursue after operational and quality baselines are stable.
**Delivers:** Backtest/replay API and optional explainability payloads with explicit latency budgets.
**Addresses:** P3 roadmap items.

### Phase Ordering Rationale

- Phase order follows strict dependency chain: **data correctness → operations correctness → model governance → quality intelligence → advanced capabilities**.
- Grouping aligns with architecture boundaries (serving path vs async validation path) and keeps p95/p99 latency risk contained.
- This sequencing directly neutralizes the highest-severity pitfalls before adding scope that increases system complexity.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Kraken account-tier rate-limit semantics and exact degraded-mode policy (hard fail vs stale-data soft fail).
- **Phase 3:** Model artifact compatibility matrix and MLflow rollout policy design for this repo’s training cadence.
- **Phase 4:** Drift/calibration threshold selection and label-latency-aware evaluation windows.

Phases with standard patterns (likely skip `/gsd-research-phase`):
- **Phase 2:** FastAPI middleware, Redis distributed limits, OTel/Prometheus instrumentation are well-established patterns.
- **Core of Phase 1 (HTTP resilience mechanics):** timeout/retry/circuit-breaker implementation patterns are mature and documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Mostly official docs + Context7 + concrete version guidance; minor uncertainty on ancillary package drift tools. |
| Features | MEDIUM | Strong industry pattern alignment, but some differentiators depend on product strategy and user segment choices. |
| Architecture | HIGH | Clear, standard FastAPI production patterns with strong source support and good fit to brownfield repo. |
| Pitfalls | HIGH | Directly tied to Kraken/scikit-learn/FastAPI operational realities; high practical relevance. |

**Overall confidence:** HIGH

### Gaps to Address

- **Kraken historical data limits vs business recovery objectives:** define exact RPO/RTO policy and whether secondary data source is required.
- **Authentication strategy choice (API key vs JWT):** decide based on client mix (internal-only vs external multi-tenant).
- **Degraded-mode product policy:** formalize when to return non-200 vs 200 with `degraded=true`, and make this contractual.
- **Label availability latency:** define evaluation cadence and acceptance gates for drift/calibration metrics.
- **Performance budgets:** set explicit p95/p99 SLO targets before enabling heavier optional response payloads.

## Sources

### Primary (HIGH confidence)
- FastAPI docs (larger apps, middleware, lifespan, deployment patterns)
- OpenTelemetry Python docs + Prometheus client Python docs
- Kraken docs (OHLC semantics + rate limits)
- scikit-learn docs (model persistence and data leakage pitfalls)
- MLflow docs (alias-based model promotion, stage deprecation)

### Secondary (MEDIUM confidence)
- Evidently docs (drift/quality monitoring workflows)
- Cloud reference patterns: AWS SageMaker monitoring/variants, Azure ML endpoint routing/monitoring
- Currency/FX API ecosystem docs for quota/error expectation benchmarking

### Tertiary (LOW confidence)
- Explainability-as-response differentiator assumptions for this exact model/runtime mix (requires implementation validation)

---
*Research completed: 2026-04-11*
*Ready for roadmap: yes*
