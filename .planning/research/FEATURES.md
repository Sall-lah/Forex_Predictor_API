# Feature Research

**Domain:** Forex prediction API for developers and automated trading workflows
**Researched:** 2026-04-11
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Deterministic prediction contract (strict request/response schema + versioned endpoint) | Bot workflows break on schema drift; developers expect stable contracts | MEDIUM | Keep `prediction`, `probabilities`, `pair`, `timeframe`, `model_version`, `timestamp` explicit and typed. (Confidence: HIGH) |
| Health, readiness, and dependency status endpoints | Automation platforms need machine-checkable service state for orchestration/restarts | LOW | Split liveness vs readiness; readiness should fail when model artifact or upstream market-data dependency is unavailable. (HIGH) |
| Consistent error taxonomy and HTTP semantics | Workflow engines route retries/escalations based on status code and error code | MEDIUM | Separate validation errors (4xx), upstream transient errors (5xx/502/503), and model-runtime errors with stable `error_code`. (HIGH) |
| Request timeouts, retries, and circuit-breaker behavior for market-data provider calls | External data providers are failure-prone; APIs must degrade predictably | MEDIUM | Add bounded timeout + retry policy + fallback behavior (`stale_data`, `partial_unavailable`) instead of hanging requests. (MEDIUM) |
| Rate limiting and quota visibility | Public API consumers assume per-key/per-client rate limits and actionable feedback headers | MEDIUM | Return remaining quota/reset metadata so clients can self-throttle. (MEDIUM) |
| Core observability (request count, latency histograms, error rate, in-progress requests) | Production API reliability requires SLOs/alerting, not just logs | MEDIUM | Expose Prometheus-style metrics (`Counter`, `Histogram`, `Gauge`) and correlate with request IDs. (HIGH) |
| Model and data freshness metadata in every prediction | Consumers need to know if prediction used recent data and which model generated it | LOW | Include `data_timestamp`, `prediction_timestamp`, `model_version`, optional `feature_window_end`. (MEDIUM) |
| Authentication and basic usage governance | Developer-facing APIs are expected to protect endpoints and support multi-client usage policies | MEDIUM | API key/JWT + per-client limits + audit trail; no auth is acceptable only for internal-only deployments. (LOW for mandatory auth in this specific repo, HIGH for external API norm) |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Online model-quality monitoring (prediction drift + outcome quality drift) | Moves API from “signal feed” to “trustworthy decision input” with early warning before silent quality decay | HIGH | Baseline + scheduled drift checks + alert hooks. Mirrors managed offerings like SageMaker Model Monitor. (MEDIUM) |
| Champion–challenger / shadow prediction mode | Enables safe model upgrades with real traffic before full cutover | HIGH | Return primary prediction while logging shadow model outputs for offline comparison; supports progressive rollout. (HIGH) |
| Calibration + confidence diagnostics endpoint | Helps users decide when NOT to trade and set confidence thresholds programmatically | MEDIUM | Publish rolling Brier score / calibration bins / hit-rate by confidence bucket. (MEDIUM) |
| Backtest/replay API for strategy validation | Lets developers validate model behavior on historical windows using same inference contract | HIGH | Critical for workflow trust before live automation. Keep separate from online prediction latency path. (MEDIUM) |
| Explainability payloads (lightweight feature contribution summary) | Increases operator trust and accelerates debugging of regime changes | HIGH | Optional field/endpoint; keep compact to avoid latency bloat. (LOW-MEDIUM, depends on model type/artifacts) |
| Reliability SLO endpoint/reporting (uptime, p95 latency, data-lag SLA) | Enterprise integrators choose vendors with measurable reliability guarantees | MEDIUM | Expose rolling SLO attainment and incident status feed. (MEDIUM) |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| “One endpoint does everything” (train + backtest + infer + admin ops) | Seems convenient and fast to ship | Couples latency-critical inference to heavy/offline workloads; harder to scale and secure | Keep inference API narrow; move retraining/backtests/admin to separate async/internal endpoints |
| Unbounded real-time streaming/WebSocket-first design from day one | Perceived as “more real-time” | Adds ops complexity (stateful infra, fan-out, backpressure) before reliability basics are mature | Start with robust pull-based HTTP + webhooks; add streaming only after proven demand |
| Overly granular feature toggles per request (custom indicators/model params each call) | Promises flexibility for quants | Breaks reproducibility, increases abuse risk, and complicates model validation | Offer curated model profiles/tiers with explicit versioning |
| Returning raw provider payloads directly to users | Saves transformation effort | Leaks provider schema instability upstream; breaks client contracts on provider changes | Normalize provider data into internal canonical schema before serving |

## Feature Dependencies

```
[Stable Prediction Contract]
    └──requires──> [Error Taxonomy]
    └──requires──> [Model/Data Freshness Metadata]

[Readiness Endpoint]
    └──requires──> [Dependency Checks: model artifact + market data provider]

[Rate Limiting & Auth]
    └──requires──> [Client Identity]

[Core Observability]
    └──enables──> [SLO Reporting]
    └──enables──> [Drift/Quality Alerting]

[Champion-Challenger / Shadow Mode]
    └──requires──> [Model Versioning]
    └──requires──> [Prediction Logging + Offline Evaluation Pipeline]

[Calibration Diagnostics]
    └──requires──> [Outcome Label Ingestion]
    └──requires──> [Historical Prediction Store]

[Backtest/Replay API]
    └──requires──> [Historical Data Access]
    └──requires──> [Reproducible Feature Pipeline]
```

### Dependency Notes

- **Core observability enables SLO and quality monitoring:** without latency/error/request metrics, there is no defensible “production ready” claim.
- **Champion-challenger requires model versioning + logging:** safe rollout is impossible if predictions cannot be attributed to exact model versions.
- **Calibration diagnostics require realized outcomes:** confidence quality can’t be validated from predictions alone.
- **Readiness must include external dependencies:** liveness-only checks create false “healthy” signals during provider/model outages.

## MVP Definition

### Launch With (v1)

Minimum viable product — what’s needed to support reliable automated usage.

- [ ] Deterministic prediction schema + explicit model/data timestamps — baseline contract stability for bots
- [ ] Health/readiness split with dependency-aware readiness — safe automation and deployment behavior
- [ ] Structured error taxonomy + retry-safe failure semantics — reliable client retry/orchestration logic
- [ ] Timeouts/retries/circuit-breaker for upstream data calls — prevents hangs and cascading failures
- [ ] Core metrics + request IDs + centralized logs — minimum observability for incident response
- [ ] Rate limiting with quota feedback headers — protects service while enabling client-side pacing

### Add After Validation (v1.x)

Features to add once core reliability is proven in production.

- [ ] Champion–challenger/shadow predictions — add when model iteration cadence increases
- [ ] Drift and model-quality monitors with alerts — add when enough live outcome data is accumulated
- [ ] SLO status reporting endpoint — add once SLO targets are measured consistently for several weeks

### Future Consideration (v2+)

Features to defer until product behavior is stable and trusted.

- [ ] Backtest/replay API using production inference contract — defer until historical storage and reproducibility are hardened
- [ ] Explainability response payloads — defer until latency budget and model-compatibility constraints are clear

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Deterministic prediction contract | HIGH | MEDIUM | P1 |
| Health/readiness with dependency checks | HIGH | LOW | P1 |
| Error taxonomy and failure semantics | HIGH | MEDIUM | P1 |
| Upstream timeout/retry/circuit breaker | HIGH | MEDIUM | P1 |
| Core observability metrics | HIGH | MEDIUM | P1 |
| Rate limiting + quota feedback | HIGH | MEDIUM | P1 |
| Champion-challenger/shadow mode | HIGH | HIGH | P2 |
| Drift/model-quality monitoring | HIGH | HIGH | P2 |
| SLO reporting endpoint | MEDIUM | MEDIUM | P2 |
| Backtest/replay API | MEDIUM | HIGH | P3 |
| Explainability payloads | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature Pattern | Ecosystem Example A | Ecosystem Example B | Recommended Approach for This Project |
|----------------|---------------------|---------------------|----------------------------------------|
| Safe model rollout | SageMaker production variants support traffic split and target variant invocation | Azure ML online endpoints support multi-deployment traffic routing + mirroring | Implement app-level shadow mode first, then weighted rollout mechanism |
| Production monitoring | SageMaker Model Monitor supports data/model quality drift scheduling and alerts | Azure ML integrates endpoint metrics/logs with Azure Monitor and autoscaling | Start with first-party metrics + alerting; add drift monitors after prediction/outcome history exists |
| API governance | Currency/market APIs commonly document rate limits, status codes, and quotas | (Observed across FX data API docs) | Standardize clear quota behavior and error docs early |

## Sources

- Project context: `.planning/PROJECT.md` (repo-local, HIGH)
- FastAPI docs (exception handling, middleware, schema/OpenAPI patterns): https://github.com/fastapi/fastapi/tree/master/docs (via Context7, HIGH)
- Prometheus Python client docs (Counter/Histogram/Gauge instrumentation patterns): https://github.com/prometheus/client_python (via Context7, HIGH)
- AWS SageMaker Model Monitor (data/model quality monitoring): https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html (HIGH)
- AWS SageMaker production variants/A-B testing: https://docs.aws.amazon.com/sagemaker/latest/dg/model-ab-testing.html (HIGH)
- Azure ML online endpoints (traffic routing/mirroring, monitoring, autoscale): https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints-online?view=azureml-api-2 (HIGH)
- CurrencyAPI docs index (rate limit/quota/status-doc expectations): https://currencyapi.com/docs (MEDIUM)
- Alpha Vantage docs (FX endpoints and premium/realtime entitlement patterns): https://www.alphavantage.co/documentation/ (MEDIUM)

---
*Feature research for: Forex prediction API*
*Researched: 2026-04-11*
