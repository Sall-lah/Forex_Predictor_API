# Stack Research

**Domain:** Python FastAPI ML inference pipeline (time-series / market prediction)
**Researched:** 2026-04-09
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12.x | Runtime for API + inference | Matches current repo/runtime, broad wheel support for pandas/numpy/sklearn/lightgbm, and stable typing/perf for service code. |
| FastAPI | 0.135.3 | API boundary and dependency wiring | Current FastAPI guidance favors `lifespan` for startup/shutdown resource management (model load/unload), which is exactly what reliable inference services need. |
| Uvicorn | 0.44.0 | ASGI serving | Production controls (`--workers`, concurrency/resource/timeouts, proxy trust controls) are explicit and mature for prediction APIs under burst load. |
| Pydantic | 2.12.5 | Request/response and contract validation | Strict mode + `extra='forbid'` enables hard failure on malformed/misaligned payloads instead of silent coercion. |
| pandas | 3.0.2 | Deterministic feature engineering | Standard tabular/time-series transform layer for rolling/EWM features and NaN handling before inference. |
| numpy | 2.4.4 | Numeric backend | Required by pandas/sklearn/lightgbm; modern 2.x performance baseline for inference preprocessing. |
| scikit-learn | 1.8.0 | Pipeline contract + persistence conventions | Canonical guidance for preventing train/serve skew via `Pipeline`; feature metadata (`n_features_in_`, `feature_names_in_`) supports robust input checks. |
| LightGBM | 4.6.0 | Model inference engine | Strong fit for tabular market features and already in-project; native support for missing values and efficient prediction throughput. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| joblib | 1.5.3 | Model artifact loading/persistence | Use for trusted internal artifacts and faster loading / memory-mapped sharing across workers (`mmap_mode='r'`). |
| httpx | 0.28.1 | Upstream market data client | Use for resilient OHLCV retrieval with explicit timeout/retry policy and typed error mapping. |
| ta | 0.11.0 | Technical indicators | Keep for milestone compatibility with existing preprocessing; avoid expanding dependency footprint unless indicators are fully contract-tested. |
| pandera | 0.x (latest stable) | DataFrame schema guardrail (optional but recommended) | Add when you need explicit DataFrame-level validation (required columns/order/dtypes/nullability) between preprocessing and model predict. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest + pytest-cov + pytest-mock | Inference contract regression tests | Add fixture-driven tests for feature completeness, ordering, and failure paths (missing/extra/misordered columns). |
| pip-tools (or conda-lock) | Reproducible dependency locks | Pin exact transitive versions to keep train/serve environment parity for sklearn/joblib artifacts. |

## Implementation Approach (2025 standard for this milestone)

1. **Single inference contract object** (source of truth): ordered feature list + dtypes + nullability rules.
2. **Preprocess into DataFrame, then validate hard** (Pydantic/Pandera + explicit column checks).
3. **Reindex to model feature order** before `predict`.
4. **Fail closed**: if any required feature missing/mismatched, raise domain validation error (422), do not infer.
5. **Load model in FastAPI lifespan** (not per request), keep immutable singleton per worker.
6. **Run Uvicorn with explicit production limits** (`--workers`, `--limit-concurrency`, `--timeout-*`, trusted proxy config).
7. **Pin artifact + runtime versions together** (record sklearn/numpy/lightgbm/joblib versions with model metadata).

## Installation

```bash
# Runtime
pip install \
  "fastapi==0.135.3" "uvicorn==0.44.0" \
  "pydantic==2.12.5" "pydantic-settings==2.13.1" \
  "pandas==3.0.2" "numpy==2.4.4" \
  "scikit-learn==1.8.0" "lightgbm==4.6.0" \
  "joblib==1.5.3" "httpx==0.28.1" "ta==0.11.0"

# Optional strict DataFrame contract layer
pip install pandera

# Dev / test
pip install -D pytest pytest-cov pytest-mock pip-tools
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| joblib (trusted internal artifact flow) | skops.io | Prefer when artifact provenance is less trusted and you want safer load semantics than pickle-based formats. |
| Python object inference (LightGBM/sklearn in-process) | ONNX runtime | Use when you need non-Python serving environment or tighter memory footprint and your model/pipeline is fully convertible. |
| Existing `ta` usage (for this milestone) | Re-implement indicators directly in pandas/numpy | Use when you need full transparency/version control over every feature formula and want to remove stale third-party indicator dependency risk. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Loading untrusted `.pkl`/`.joblib` artifacts | Pickle-based loaders can execute arbitrary code; security risk. | Trusted artifact pipeline only, or `skops.io` for stricter loading. |
| Implicit feature alignment ("whatever columns are present") | Causes silent train/serve skew and invalid predictions. | Explicit required feature contract + strict validation + deterministic reindexing. |
| FastAPI `startup` / `shutdown` events for new resource lifecycle code | Current FastAPI docs recommend `lifespan`; events are legacy/deprecated path. | `FastAPI(lifespan=...)` with model init/cleanup there. |
| Unpinned dependency ranges in inference services | Breaks artifact compatibility across deployments (sklearn/numpy/joblib drift). | Fully pinned versions and lock files per release. |
| LightGBM shape-check bypass (`predict_disable_shape_check=true`) | Disables safety net for feature-count mismatch. | Keep default safety checks ON and enforce explicit feature checks before predict. |

## Stack Patterns by Variant

**If keeping current LightGBM artifact (this milestone):**
- Use pandas/numpy preprocessing + strict contract validator + in-process LightGBM inference.
- Because lowest migration risk and directly solves feature-alignment reliability issues.

**If moving to hardened artifact security later:**
- Use skops/ONNX evaluation track in a dedicated phase.
- Because security/portability improvements require conversion/testing that is beyond this milestone’s scope.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| scikit-learn==1.8.0 | numpy==2.4.4, joblib==1.5.3 | Keep training and serving versions aligned; sklearn warns on inconsistent model versions. |
| lightgbm==4.6.0 | pandas 2.x/3.x, numpy 2.x | Validate model I/O path in CI after upgrades; keep feature count checks enabled. |
| fastapi==0.135.3 | pydantic==2.12.5 | Modern FastAPI stack expects Pydantic v2 behavior. |
| ta==0.11.0 | pandas/numpy recent versions (project-tested required) | Last release is older; keep regression tests around indicator outputs. |

## Confidence by Recommendation Area

| Area | Confidence | Reason |
|------|------------|--------|
| FastAPI lifecycle + serving pattern | HIGH | Verified in current FastAPI and Uvicorn docs. |
| Feature-contract enforcement approach | HIGH | Backed by sklearn pipeline/common-pitfalls guidance + LightGBM shape-check behavior. |
| Persistence/security recommendations | HIGH | Directly from sklearn model persistence documentation. |
| `ta` long-term suitability | MEDIUM | Package is stable but older; recommendation is conservative (keep now, limit expansion). |

## Sources

- Context7 `/fastapi/fastapi` — lifespan pattern and startup/shutdown guidance (HIGH)
- Context7 `/kludex/uvicorn` + https://www.uvicorn.org/settings/ — worker/resource/proxy/timeouts (HIGH)
- Context7 `/pydantic/pydantic` — strict validation/config patterns (HIGH)
- Context7 `/scikit-learn/scikit-learn` + https://scikit-learn.org/stable/model_persistence.html — pipeline reliability + persistence/security/version constraints (HIGH)
- Context7 `/lightgbm-org/lightgbm` + https://lightgbm.readthedocs.io/en/stable/Python-API.html — inference APIs and shape-check parameter behavior (MEDIUM-HIGH; shape-check detail from parameters docs)
- Context7 `/pandas-dev/pandas` — rolling/EWM time-series feature engineering patterns (HIGH)
- Context7 `/unionai-oss/pandera` — DataFrame schema validation option for inference contracts (MEDIUM)
- PyPI JSON API (queried 2026-04-09) — current package versions and release recency (HIGH)

---
*Stack research for: Forex Predictor API prediction-alignment milestone*
*Researched: 2026-04-09*
