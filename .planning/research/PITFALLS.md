# Pitfalls Research

**Domain:** ML-based forex prediction API operations (FastAPI + Kraken OHLC + LightGBM/scikit-learn)
**Researched:** 2026-04-11
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Training/Serving on Incomplete Candles

**What goes wrong:**
Teams include Kraken’s latest OHLC row as if it were final. That row is explicitly the *current, not-yet-committed* candle, so features/labels become unstable and predictions oscillate.

**Why it happens:**
Polling code assumes “last row is newest truth” and skips exchange-specific semantics.

**How to avoid:**
- In ingestion and prediction feature prep, drop the last OHLC row unless timestamp < (now - interval).
- Use Kraken `result.last` as the next `since` cursor for committed updates.
- Add a contract test that asserts incomplete candle exclusion.

**Warning signs:**
- Prediction flips direction rapidly within the same interval without major market move.
- Backtests look much better than live performance.
- Feature values near candle boundary show abrupt reversals.

**Phase to address:**
Phase 1 — Data Reliability Hardening (upstream contract correctness before any model changes).

---

### Pitfall 2: Assuming Kraken OHLC Supports Deep Backfill

**What goes wrong:**
Teams design recovery/backfill expecting arbitrary history from Kraken OHLC. Kraken returns up to 720 recent entries, so outages create unrecoverable gaps if no secondary storage exists.

**Why it happens:**
`since` parameter is treated as full historical cursor, not bounded rolling window.

**How to avoid:**
- Persist raw OHLC snapshots internally (DB/object storage) as system-of-record.
- Define explicit outage recovery policy: if gap > 720 candles, mark prediction quality degraded.
- Add “data completeness” checks before inference.

**Warning signs:**
- Sudden holes in feature windows after downtime.
- Rebooted service cannot reconstruct required lookback period.
- Silent fallback to smaller windows without explicit error/degradation flag.

**Phase to address:**
Phase 1 — Data Reliability Hardening.

---

### Pitfall 3: Upstream Rate-Limit/Outage Cascades

**What goes wrong:**
When Kraken returns throttling/errors, API instances retry aggressively or fail synchronously, causing latency spikes and cascading 5xx responses.

**Why it happens:**
No jittered backoff, no circuit breaker, and no stale-data fallback path.

**How to avoid:**
- Implement bounded retries with exponential backoff + jitter.
- Add circuit breaker around Kraken client; fail fast while open.
- Serve last-known-good feature snapshot with explicit `degraded=true` metadata when policy allows.
- Define SLO-aware timeout budgets per endpoint.

**Warning signs:**
- Burst of 429 / upstream timeout errors.
- P95 latency rises sharply before outright failures.
- Worker saturation during Kraken incidents.

**Phase to address:**
Phase 1 — Reliability and Failure-Mode Hardening.

---

### Pitfall 4: Process-Local Rate Limiting in Multi-Worker Deployments

**What goes wrong:**
Scaling to multiple workers/instances bypasses true global quota enforcement because each process tracks limits independently.

**Why it happens:**
In-memory bucket state is not shared across processes.

**How to avoid:**
- Move limiter storage to Redis (or API gateway-level quota enforcement).
- Key limits by authenticated principal (API key), not only IP.
- Add distributed load test verifying global cap behavior.

**Warning signs:**
- Effective allowed request rate increases with worker count.
- “Abusive” clients pass by rotating connections across instances.
- Inconsistent throttling decisions between pods.

**Phase to address:**
Phase 2 — Security and Traffic Control.

---

### Pitfall 5: Model Artifact Compatibility Drift

**What goes wrong:**
Serialized model loads with warnings or breaks after dependency updates; worst case is silent prediction behavior drift.

**Why it happens:**
Unpinned runtime/training dependencies and weak artifact metadata/version checks.

**How to avoid:**
- Pin training + serving dependency matrix and store with artifact metadata.
- Fail startup on version mismatch (don’t suppress `InconsistentVersionWarning` in production path).
- Introduce artifact manifest: model version, sklearn/lightgbm versions, feature schema hash, training data snapshot ID.

**Warning signs:**
- Startup warnings around estimator version mismatch.
- Prediction distribution shift after innocuous deploy.
- “Works in dev, fails in prod” model loading behavior.

**Phase to address:**
Phase 2 — Model Lifecycle and Release Governance.

---

### Pitfall 6: Feature Schema Drift Between Training and Inference

**What goes wrong:**
Column name/order drift (including typo fixes) breaks model input contract, causing hard failures or wrong predictions.

**Why it happens:**
Feature engineering evolves without a versioned schema contract and migration tests.

**How to avoid:**
- Treat feature schema as versioned API contract.
- Validate exact required feature set and order before inference.
- Add migration harness: old artifact + new pipeline compatibility test.

**Warning signs:**
- Missing/extra feature exceptions after refactors.
- Sudden drop in confidence calibration without upstream data change.
- Frequent hotfixes around feature name mismatches.

**Phase to address:**
Phase 2 — Model Contract Hardening.

---

### Pitfall 7: Time-Series Leakage in Validation

**What goes wrong:**
Offline metrics look excellent, but live performance underperforms because evaluation leaked future information.

**Why it happens:**
Random splits or preprocessing fitted on full dataset before split.

**How to avoid:**
- Use walk-forward or `TimeSeriesSplit` validation only.
- Fit preprocessing strictly on train folds via sklearn `Pipeline`.
- Gate releases on forward-window performance and calibration thresholds.

**Warning signs:**
- Large gap between backtest and live precision.
- Retrains report dramatic improvements that vanish in production.
- Postmortems identify train-time access to future rows.

**Phase to address:**
Phase 3 — Prediction Quality Assurance.

---

### Pitfall 8: No Confidence/Degradation Signaling in API Responses

**What goes wrong:**
Consumers treat all predictions as equally trustworthy, even when data is stale, lookback is incomplete, or fallback path was used.

**Why it happens:**
Response schema lacks quality metadata and failure mode encoding.

**How to avoid:**
- Add response fields: `data_freshness_seconds`, `feature_window_complete`, `model_version`, `degraded_mode`.
- Return explicit non-200 or soft-fail status based on policy when quality gates fail.
- Document consumer handling contract.

**Warning signs:**
- Client teams ask why predictions changed “randomly.”
- Incidents where stale data produced valid-looking 200 responses.
- No way to correlate bad outcomes with degraded inputs.

**Phase to address:**
Phase 3 — API Contract and Consumer Trust.

---

### Pitfall 9: Missing Authentication + Weak Abuse Attribution

**What goes wrong:**
Public prediction endpoints get scraped/abused; limits keyed only by IP are easy to evade and make tenant-level control impossible.

**Why it happens:**
Service starts as internal API and auth is deferred too long.

**How to avoid:**
- Add API key or JWT auth before broader exposure.
- Combine auth with per-principal quotas and audit logging.
- Preserve trusted proxy config carefully; trust only known proxy IPs.

**Warning signs:**
- Traffic spikes from rotating IPs.
- Inability to identify high-cost clients.
- Frequent rate-limit incidents despite “strict” settings.

**Phase to address:**
Phase 2 — Security and Access Control.

---

### Pitfall 10: Operating Without Prediction Drift Monitoring

**What goes wrong:**
Model quality degrades gradually (regime change, volatility shift) while API health remains green; teams discover failure only from downstream losses.

**Why it happens:**
Only infra metrics are tracked (latency/errors), not model performance and calibration over time.

**How to avoid:**
- Track delayed-label metrics per pair/interval: hit rate, Brier score, calibration bins.
- Define alert thresholds and retraining triggers.
- Version and compare champion/challenger models in shadow mode.

**Warning signs:**
- Stable uptime with worsening business outcomes.
- Confidence scores remain high while realized accuracy falls.
- No model-quality dashboards tied to production predictions.

**Phase to address:**
Phase 4 — Observability and Continuous Evaluation.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Data ingestion hardening | Incomplete-candle leakage | Enforce committed-candle-only rule + tests |
| Resilience implementation | Retry storm amplification | Add exponential backoff, jitter, and circuit breaker |
| Security rollout | IP-only quotas remain bypassable | Introduce principal-based auth + distributed limiter |
| Model release process | Version drift of serialized artifacts | Startup compatibility checks + pinned dependency matrix |
| Quality gates | Leakage in evaluation | TimeSeriesSplit + strict train-only preprocessing |
| API contract extension | No degradation signaling | Add freshness/completeness/degraded metadata |
| Production monitoring | Hidden model drift | Realized-performance dashboards + alerts |

## Sources

- Kraken OHLC docs (committed vs current candle, 720-entry limit): https://docs.kraken.com/api/docs/rest-api/get-ohlc-data (HIGH)
- Kraken Spot REST rate limits: https://docs.kraken.com/api/docs/guides/spot-rest-ratelimits (HIGH)
- FastAPI deployment behind proxy / forwarded headers trust: https://fastapi.tiangolo.com/advanced/behind-a-proxy/ (HIGH)
- FastAPI lifespan events for startup/shutdown resource handling: https://fastapi.tiangolo.com/advanced/events/ (HIGH)
- scikit-learn model persistence limitations and version/security warnings: https://scikit-learn.org/stable/model_persistence.html (HIGH)
- scikit-learn common pitfalls (data leakage, pipelines): https://scikit-learn.org/stable/common_pitfalls.html (HIGH)
- Repository-specific operational concerns audit: `.planning/codebase/CONCERNS.md` and `.planning/codebase/INTEGRATIONS.md` (HIGH)

---
*Pitfalls research for: Forex prediction API (production hardening + extension)*
*Researched: 2026-04-11*
