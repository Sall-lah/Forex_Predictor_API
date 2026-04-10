# Feature Research

**Domain:** ML prediction API reliability (feature-engineered inference pipelines)
**Researched:** 2026-04-09
**Confidence:** MEDIUM-HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or unsafe for production.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Strict inference schema contract enforcement** (exact feature names, types, and column order) | Tree/GBM models are highly sensitive to feature drift; wrong order or missing columns yields invalid outputs or runtime failure | MEDIUM | Enforce against a single canonical expected-feature list from model metadata (`MODEL_USAGE.md`). Reject on missing/extra/misordered columns before `predict_proba`. |
| **Pre-inference feature completeness + null/NaN guardrails** | Rolling indicators often create NaNs; users expect API to fail safely, not infer on partial vectors | MEDIUM | Validate min history, no NaN/inf in required feature slice, and deterministic handling for warm-up rows. |
| **Clear confidence output contract** (class probabilities + predicted class) | Prediction APIs are expected to return uncertainty, not only a label | LOW-MEDIUM | Return all class probabilities and document class mapping. Keep probability schema stable. |
| **Failure clarity with actionable 4xx/5xx taxonomy** | Integrators need to distinguish client-fixable schema errors from upstream or model-availability errors | LOW-MEDIUM | Use structured errors (`code`, `detail`, `action`, `request_id`), mapped to domain exceptions and HTTP status codes. |
| **Baseline observability** (request IDs, structured logs, latency/error metrics) | Production API operations require debuggability and SLO tracking | MEDIUM | Log prediction lifecycle and failure reason codes; expose counters/histograms via Prometheus and/or OTel. |
| **Contract regression tests for training-vs-serving alignment** | Reliability regressions usually come from silent feature changes | MEDIUM | Add tests that assert exact expected columns/order/count and fail CI on drift. |

### Differentiators (Competitive Advantage)

Features that improve trust and operability beyond table stakes.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Calibrated confidence with calibration metadata** (e.g., method, version, evaluation date) | Makes probabilities decision-grade instead of raw model scores | HIGH | Use post-training calibration workflow and expose calibration status in response metadata/docs. |
| **Prediction reliability envelope** (provenance: model version, feature schema hash, data window timestamps) | Enables forensic debugging, reproducibility, and safer incident response | MEDIUM | Include lightweight metadata fields in response headers/body without breaking existing surface. |
| **Reliability reason codes dashboard** (schema_mismatch, insufficient_history, upstream_data_failure, model_unavailable) | Fast MTTR and better stakeholder communication | MEDIUM | Aggregate error classes in metrics; tie logs + traces via request ID / trace ID. |
| **Degraded-mode policy** (explicit fail-closed vs fallback behavior by failure type) | Prevents accidental “best-effort” predictions that look valid but are unsafe | MEDIUM-HIGH | Policy-driven behavior: e.g., no fallback on schema mismatch; optional cached-data fallback on transient fetch failures if clearly labeled. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem appealing but reduce reliability or trust.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Silent auto-fixing of feature mismatches** (auto-drop/auto-fill/auto-reorder unknown inputs) | “Keep API always responding” | Produces plausible but invalid predictions; hides training-serving skew until incidents occur | Hard fail with explicit mismatch diagnostics and remediation steps |
| **Single opaque “confidence” scalar without calibration context** | Simpler client UI | Encourages over-trust; score may be uncalibrated and misinterpreted | Return class probability vector + calibration metadata + threshold guidance |
| **Raw traceback or generic “prediction failed” errors** | Fast implementation | Either leaks internals/security details or gives no actionable fix path | Structured domain errors with stable codes and user-action hints |

## Feature Dependencies

```text
[Strict inference schema contract enforcement]
    └──requires──> [Canonical expected-feature registry from training artifact/docs]
                        └──requires──> [Contract regression tests in CI]

[Failure clarity taxonomy]
    └──requires──> [Domain exception mapping + standardized error payload]

[Baseline observability]
    └──requires──> [Request ID propagation]
                        └──enhances──> [Failure clarity taxonomy]

[Calibrated confidence with metadata]
    └──requires──> [Stable confidence output contract]
                        └──requires──> [Schema contract enforcement]

[Degraded-mode policy]
    └──conflicts──> [Silent auto-fixing of feature mismatches]
```

### Dependency Notes

- **Schema enforcement requires a canonical expected-feature registry:** without a single source of truth (names/order/types), runtime checks become brittle and inconsistent.
- **Calibration features require stable confidence outputs first:** calibration metadata is only meaningful once output semantics are fixed and documented.
- **Observability enhances failure clarity:** request IDs + reason-coded metrics make error payloads operationally useful, not just descriptive.
- **Degraded-mode conflicts with silent auto-fixing:** safe degradation must be explicit and policy-based, never implicit data mutation.

## MVP Definition

### Launch With (v1)

Minimum viable reliability for this milestone.

- [x] **Strict schema + ordering enforcement at inference boundary** — core requirement to prevent invalid predictions.
- [x] **Actionable failure responses (clear 422/502/503 semantics)** — required for client remediation and supportability.
- [x] **Probability output contract + class mapping docs** — required to make results interpretable.
- [x] **Baseline observability (request ID, structured logs, latency/error metrics)** — required for production operations.
- [x] **Alignment regression tests in CI** — required to prevent reintroducing drift.

### Add After Validation (v1.x)

- [ ] **Reliability reason-code dashboard** — add once baseline metrics are emitting consistently.
- [ ] **Prediction provenance envelope (model/schema hash/timestamps)** — add once response metadata shape is agreed.

### Future Consideration (v2+)

- [ ] **Calibrated probabilities with periodic recalibration workflow** — defer until enough evaluation data and monitoring loops exist.
- [ ] **Policy-driven degraded mode with explicit fallback labels** — defer until reliability SLAs and risk posture are finalized.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Strict schema + ordering enforcement | HIGH | MEDIUM | P1 |
| Failure clarity taxonomy | HIGH | LOW-MEDIUM | P1 |
| Baseline observability | HIGH | MEDIUM | P1 |
| Confidence output contract (all class probabilities + mapping) | HIGH | LOW-MEDIUM | P1 |
| Contract regression tests | HIGH | MEDIUM | P1 |
| Reliability reason-code dashboard | MEDIUM-HIGH | MEDIUM | P2 |
| Prediction provenance envelope | MEDIUM-HIGH | MEDIUM | P2 |
| Calibrated confidence + metadata | HIGH (for advanced users) | HIGH | P3 |
| Degraded-mode policy engine | MEDIUM | MEDIUM-HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Typical Internal/Enterprise ML APIs | Common Retail/Lightweight Prediction APIs | Our Approach |
|---------|--------------------------------------|--------------------------------------------|--------------|
| Feature schema enforcement | Strong contract checks, often with schema registries | Often partial/implicit checks | Enforce exact names/order/types at inference boundary |
| Confidence output | Full class probs, sometimes calibrated | Often single score/label only | Return full class probabilities with explicit mapping |
| Observability | Structured telemetry + reason-coded alerts | Basic logs only | Baseline telemetry in v1; reason-code views in v1.x |
| Failure clarity | Domain codes + actionable messages | Generic 500/422 messages | Stable error taxonomy with remediation hints |

## Sources

- `app/features/prediction/ml_models/MODEL_USAGE.md` (repo) — expected same feature set and order for prediction (**HIGH**)
- `app/features/prediction/ml_models/OHLCV_PREPROCESS.md` (repo) — engineered indicator definitions and rolling-window characteristics (**HIGH**)
- `/pydantic/pydantic` via Context7 — strict mode, `extra='forbid'`, structured validation errors (**HIGH**)
- `/fastapi/fastapi` via Context7 — custom exception handlers and `RequestValidationError` handling (**HIGH**)
- `/scikit-learn/scikit-learn` via Context7 — probability calibration via `CalibratedClassifierCV` and calibration caveats (**HIGH**)
- `/lightgbm-org/lightgbm` via Context7 — classifier `predict_proba` behavior for class probabilities (**MEDIUM-HIGH**)
- `/open-telemetry/opentelemetry-python` via Context7 — traces/metrics/log correlation patterns (**HIGH**)
- `/prometheus/client_python` via Context7 — counters/histograms and ASGI instrumentation patterns (**HIGH**)

---
*Feature research for: prediction feature alignment reliability milestone*
*Researched: 2026-04-09*
