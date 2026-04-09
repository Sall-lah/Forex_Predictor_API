# Architecture Research

**Domain:** FastAPI-based market prediction API (preprocessing/model-alignment hardening)
**Researched:** 2026-04-09
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ API Boundary (FastAPI)                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│  Prediction Router  │  Global Exception Handlers  │  RateLimit Middleware   │
└──────────────┬───────────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────────────┐
│ Prediction Orchestration Layer                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ Request Normalizer → OHLCV Fetcher → Preprocess Pipeline → Contract Guard   │
│                                   ↓                                         │
│                           Inference Engine                                  │
│                                   ↓                                         │
│                    Fallback Policy + Response Mapper                        │
└──────────────┬───────────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────────────┐
│ Artifacts & State                                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│ Model Bundle (model.pkl + feature_contract.json + preprocess_manifest.json) │
│ In-memory model cache + compatibility metadata                               │
│ Optional fallback model bundle(s)                                            │
│ Structured logs + metrics + drift/alignment counters                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Prediction Router | HTTP boundary only, request/response schema validation | `app/features/prediction/router.py` + `Depends()` |
| Prediction Orchestrator | Coordinates full workflow and enforces order of operations | `PredictionService` split into explicit steps |
| Preprocess Pipeline | Deterministic feature generation from OHLCV | Pure functions / pipeline object, no hidden state |
| Feature Contract Guard | Verifies required columns, dtypes, order, null policy | Contract object + validator (`validate_and_align(df)`) |
| Model Compatibility Guard | Confirms artifact/model can consume aligned features | Uses model metadata + LightGBM feature checks |
| Inference Engine | Calls model predict/predict_proba with strict input | Thin wrapper over loaded model |
| Fallback Policy Engine | Decides fail-closed vs compatible fallback model vs degraded output | Policy class w/ explicit decision matrix |
| Model Bundle Loader | Atomically loads model + contract + manifest | Startup loader + thread-safe cache |
| Telemetry/Audit | Emits structured events for every guard/fallback decision | Logging + counters + trace IDs |

## Recommended Project Structure

```text
app/
├── features/
│   └── prediction/
│       ├── router.py                          # HTTP endpoint, DI wiring only
│       ├── schemas.py                         # Request/response schemas
│       ├── service.py                         # PredictionOrchestrator facade
│       ├── contracts/
│       │   ├── feature_contract.py            # feature list/order/dtype contract
│       │   ├── model_compatibility.py         # model + contract compatibility checks
│       │   └── fallback_policy.py             # failover decision logic
│       ├── pipeline/
│       │   ├── ohlcv_preprocess.py            # deterministic feature extraction
│       │   ├── feature_alignment.py           # reorder/select/cast exactly as contract
│       │   └── validators.py                  # NaN/range/shape validation
│       ├── inference/
│       │   ├── model_bundle_loader.py         # load model + sidecar metadata
│       │   └── predictor.py                   # strict predict_proba wrapper
│       └── ml_models/
│           ├── lightgbm_model_forex.pkl
│           ├── feature_contract.json          # canonical ordered feature schema
│           ├── preprocess_manifest.json       # preprocessing version + settings
│           ├── MODEL_USAGE.md
│           └── OHLCV_PREPROCESS.md
├── shared/
│   └── ohlcv/                                 # Kraken transport + DataFrame parsing
└── core/
    ├── config.py                              # feature/model policy flags
    └── exceptions.py                          # domain exceptions mapped globally
```

### Structure Rationale

- **contracts/**: keeps alignment/compatibility policy independent from feature math; easiest place to add new checks without touching fetch/inference.
- **pipeline/**: keeps preprocessing deterministic and testable; every transform is explicit and reproducible.
- **inference/**: isolates model loading/runtime behavior and prevents routing/business logic from depending on LightGBM internals.

## Architectural Patterns

### Pattern 1: Model Bundle Contract (not model file alone)

**What:** Treat model + feature contract + preprocessing manifest as one deployable unit.
**When to use:** Always for production inference; mandatory when model and preprocessing evolve independently.
**Trade-offs:** Slightly more artifact management overhead, major reduction in runtime mismatch risk.

**Example:**
```python
@dataclass(frozen=True)
class ModelBundle:
    model: Any
    expected_features: list[str]          # canonical order
    expected_dtypes: dict[str, str]
    preprocess_version: str
    model_version: str
```

### Pattern 2: Deterministic Feature Alignment Gate before Inference

**What:** Build features, then pass through a single gate that validates completeness and reorders columns exactly.
**When to use:** Any tabular ML inference path where column order/names matter (LightGBM, sklearn, XGBoost).
**Trade-offs:** Added validation step adds tiny latency; prevents silent bad predictions.

**Example:**
```python
def validate_and_align(df: pd.DataFrame, contract: FeatureContract) -> pd.DataFrame:
    missing = [c for c in contract.columns if c not in df.columns]
    extra = [c for c in df.columns if c not in contract.columns]
    if missing:
        raise DataValidationError(f"Missing required features: {missing}")
    # Extra columns are ignored explicitly, never implicitly relied upon.
    aligned = df.loc[:, contract.columns].astype(contract.dtype_map)
    if aligned.isna().any().any() and not contract.allow_nan:
        raise DataValidationError("NaN found after feature alignment")
    return aligned
```

### Pattern 3: Guarded Inference with Explicit Fallback Policy

**What:** Separate "can we safely infer?" from "run inference" and "what to do if not".
**When to use:** APIs where reliability > always returning a numeric output.
**Trade-offs:** More branches to test, but failure modes become intentional and observable.

**Example:**
```python
decision = fallback_policy.evaluate(
    contract_ok=contract_ok,
    model_ok=model_ok,
    data_fresh=freshness_ok,
)

if decision == "PRIMARY":
    probs = predictor.predict_proba(aligned_df)
elif decision == "FALLBACK_MODEL":
    probs = fallback_predictor.predict_proba(aligned_df_fallback)
else:
    raise ModelNotLoadedError("No compatible model available for safe inference")
```

## Data Flow

### Request Flow

```text
POST /prediction/predict
    ↓
Router (validation + DI)
    ↓
PredictionOrchestrator
    ↓
OHLCV Fetch (KrakenAPIClient) → Parse (OHLCVDataFrame)
    ↓
Deterministic Preprocess Pipeline
    ↓
Feature Contract Guard (required + dtype + order + null policy)
    ↓
Model Compatibility Guard (bundle loaded? shape/name checks?)
    ↓
Inference Engine (predict_proba with strict checks)
    ↓
Fallback Policy (only if guard/inference failed)
    ↓
Response Mapper + telemetry
```

### State Management

```text
ModelBundleLoader (startup/lazy)
    ↓ caches
Primary ModelBundle + Optional Fallback Bundle(s)
    ↓ read-only during requests
PredictionOrchestrator
```

### Key Data Flows

1. **Primary inference path:** raw OHLCV → deterministic features → aligned feature frame → primary model prediction.
2. **Compatibility-failure path:** any missing/misaligned feature or model-contract mismatch → no primary inference call → fallback policy decision.
3. **Observability path:** each guard emits structured events (`feature_missing_count`, `compatibility_fail`, `fallback_used`) for roadmap and ops feedback.

## Build-Order Implications (Phase Boundaries)

1. **Phase A — Contract Foundation (must come first)**
   - Create `feature_contract.json` + `preprocess_manifest.json` sidecars.
   - Add model bundle loader and startup validation.
   - Why first: all later checks depend on a canonical contract source.

2. **Phase B — Deterministic Pipeline Refactor**
   - Refactor preprocessing into explicit deterministic pipeline steps.
   - Add `validate_and_align()` gate for required/order/dtype/null checks.
   - Why second: compatibility checks are meaningless without deterministic feature output.

3. **Phase C — Compatibility Guard + Strict Inference**
   - Add pre-inference guardrail layer and strict model invocation.
   - Enable LightGBM feature validation where supported (`validate_features=True` for pandas input).
   - Why third: enforce hard stop before runtime misprediction.

4. **Phase D — Fallback Policy + Error Surface**
   - Implement explicit decision matrix: `PRIMARY`, `FALLBACK_MODEL`, `FAIL_CLOSED`.
   - Map to domain exceptions and stable API error payloads.
   - Why fourth: only safe after primary-path guarantees are in place.

5. **Phase E — Test Matrix + Telemetry Hardening**
   - Add tests for missing columns, wrong order, dtype mismatch, incompatible model, fallback selection.
   - Add counters/logs for each guard and fallback branch.
   - Why last: validates and operationalizes all preceding architecture decisions.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k daily requests | Single-process app with in-memory model bundle cache is enough. |
| 1k-100k daily requests | Add warm startup load, feature-computation profiling, and optional async fetch batching/caching for OHLCV. |
| 100k+ daily requests | Separate inference worker pool, external feature store/cache, versioned model registry service, and circuit breaker around upstream market-data dependency. |

### Scaling Priorities

1. **First bottleneck:** upstream OHLCV latency/instability, not model scoring. Mitigate with caching + timeout/retry + fallback policy.
2. **Second bottleneck:** CPU cost of repeated indicator calculations. Mitigate with shared preprocessing cache and vectorized/pipeline profiling.

## Anti-Patterns

### Anti-Pattern 1: "Infer on whatever columns exist"

**What people do:** Pass latest feature row directly to model without canonical alignment.
**Why it's wrong:** Silent misordered columns produce wrong probabilities with no obvious failure.
**Do this instead:** Enforce explicit contract gate (`required + order + dtype + null policy`) before inference.

### Anti-Pattern 2: Disabling shape checks to force predictions

**What people do:** Enable LightGBM `predict_disable_shape_check=true`-style behavior globally.
**Why it's wrong:** Official docs warn this can yield incorrect predictions.
**Do this instead:** Keep strict checks enabled and fail closed or use vetted fallback model.

### Anti-Pattern 3: Silent degraded responses

**What people do:** Return fallback output without explicit telemetry/error semantics.
**Why it's wrong:** Ops and consumers cannot distinguish healthy vs degraded predictions.
**Do this instead:** Emit explicit fallback events, include deterministic policy branch, and keep exception mapping consistent.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Kraken OHLC API | HTTP client wrapper (`KrakenAPIClient`) + envelope validation | Upstream volatility is primary reliability risk; keep retries bounded. |
| Model artifact storage (local now, registry later) | ModelBundleLoader + versioned sidecar files | Bundle model + contract atomically to prevent drift. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `router.py` ↔ `service.py` | Direct DI call | Keep HTTP concerns out of service logic. |
| `service.py` ↔ `pipeline/` | Direct function/object calls | Pipeline must be deterministic/pure for reproducibility. |
| `service.py` ↔ `contracts/` | Guard calls before inference | Contract failures should raise domain errors, not generic exceptions. |
| `service.py` ↔ `inference/` | Predictor interface (`predict_proba`) | Inference called only after guards pass. |

## Sources

- Project scope and constraints: `.planning/PROJECT.md` (repo local source) — HIGH
- Current prediction architecture: `app/features/prediction/service.py`, `router.py`, `schemas.py` — HIGH
- Shared OHLCV boundaries: `app/shared/ohlcv/kraken_api.py`, `ohlc_dataframe.py` — HIGH
- FastAPI dependency injection and exception handlers: https://fastapi.tiangolo.com/tutorial/dependencies/ and https://fastapi.tiangolo.com/tutorial/handling-errors/ — HIGH
- LightGBM Booster API (`predict(..., validate_features=...)`, `feature_name()`, `num_feature()`): https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.Booster.html — HIGH
- LightGBM predict params and shape-check warning (`predict_disable_shape_check`): https://lightgbm.readthedocs.io/en/stable/Parameters.html#predict-parameters — HIGH
- Scikit-learn guidance on consistent preprocessing / leakage prevention (Pipeline best practices): https://scikit-learn.org/stable/common_pitfalls.html — HIGH

---
*Architecture research for: prediction pipeline alignment hardening*
*Researched: 2026-04-09*
