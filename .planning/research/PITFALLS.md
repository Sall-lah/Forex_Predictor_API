# Domain Pitfalls

**Domain:** Production ML API inference hardening (OHLCV preprocessing + LightGBM prediction alignment)
**Researched:** 2026-04-09
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Feature-Contract Drift Between Training and Inference

**What goes wrong:**
Inference builds a feature set that no longer matches the training contract (missing columns, extra columns, wrong names, wrong order). This can fail at runtime *or* silently produce wrong probabilities.

**Why it happens:**
- Feature definitions live in docs (`OHLCV_PREPROCESS.md`, `MODEL_USAGE.md`) but are not enforced as executable contract.
- Developers add/remove indicators without updating the model input schema.
- DataFrame column order is assumed, not enforced.

**Consequences:**
- Immediate prediction errors in production.
- Worse: silent prediction corruption when shapes happen to match but semantics differ.

**Prevention:**
- Create a **single source-of-truth model input manifest** shipped with the artifact (ordered feature list, model version, class mapping, expected dtypes).
- Before `predict_proba`, enforce exact schema:
  1. Check set equality (missing/unexpected columns).
  2. Reorder with `df = df.reindex(columns=expected_columns)`.
  3. Fail fast if any missing columns were introduced as `NaN`.
- Keep LightGBM feature checks enabled (`validate_features=True` when predicting with DataFrame).
- Add contract tests that compare preprocessor output columns to manifest on every CI run.

**Detection (warning signs):**
- Spike in `DataValidationError`/model errors right after feature code changes.
- Different column counts between environments.
- Predictions become distributionally weird without model retraining.

**Phase to address:**
Phase 1 — Feature Contract Baseline & Schema Gate

---

### Pitfall 2: Turning Off Feature Validation or Bypassing Names

**What goes wrong:**
Inference relies on raw arrays or disabled checks so feature names are ignored. Column order mistakes pass through and outputs become unreliable.

**Why it happens:**
- Teams optimize for “make it pass” by disabling shape/name checks.
- LightGBM defaults (`validate_features=False` in predict APIs) are easy to leave unchanged.
- In CLI/parameter usage, options like shape-check disablement are misunderstood as safe defaults.

**Consequences:**
- Silent corruption: valid numeric outputs with invalid feature semantics.
- Hard-to-debug incidents because no explicit exception is raised.

**Prevention:**
- Always pass pandas DataFrame with named columns (never anonymous ndarray in production inference path).
- Call `predict_proba(..., validate_features=True)`.
- Ban config patterns that disable shape/feature checks in production.
- Add static guardrail test: prediction path must set validation flag.

**Detection (warning signs):**
- Prediction code path uses `.values`/NumPy conversion before model call.
- No tests that fail on swapped column order.
- Sudden behavior changes with no exceptions and no model artifact change.

**Phase to address:**
Phase 1 — Feature Contract Baseline & Schema Gate

---

### Pitfall 3: Probability Column Misinterpretation (Class Index Assumptions)

**What goes wrong:**
API assumes “column index 1 = probability_up” permanently. If class encoding/order differs (binary vs multiclass handling, label mapping drift), response semantics break.

**Why it happens:**
- Hard-coded probability index in service logic.
- Missing persisted class mapping in model metadata.
- No post-load validation against `model.classes_` or equivalent contract.

**Consequences:**
- API returns coherent-looking but semantically wrong probabilities.
- Business consumers act on inverted/shifted signals.

**Prevention:**
- Persist explicit `class_mapping` with model artifact (e.g., `{0: Hold, 1: Buy, 2: Sell}`).
- At startup, verify expected class labels/order against loaded model metadata.
- Derive target index from class label lookup, not hardcoded numeric position.
- Add tests that intentionally shuffle/alter class order and assert failure.

**Detection (warning signs):**
- Model upgrade without class-map regression tests.
- Up/Buy probability suddenly inverts against historical behavior.
- Conflicting docs vs runtime output shape.

**Phase to address:**
Phase 2 — Inference Semantics & Output Contract Hardening

---

### Pitfall 4: Temporal Leakage and Incomplete-Candle Contamination

**What goes wrong:**
Feature generation includes incomplete current candles or future-informed aggregates, causing optimistic backtests and unstable live inference.

**Why it happens:**
- OHLCV data ingestion doesn’t enforce candle completeness.
- Rolling windows and resampling are implemented differently from training.
- Temporal cutoffs are not explicit in preprocessing.

**Consequences:**
- “Works in test, fails in prod” prediction quality collapse.
- Hidden data leakage that invalidates model behavior assumptions.

**Prevention:**
- Enforce strict time-boundary rules: only fully closed hourly candles.
- Reproduce training-time resampling/window logic exactly (same timezone, same window definitions).
- Add leakage tests: assert no feature at time *t* depends on data after *t*.
- Keep a reproducible offline parity test using frozen OHLCV fixtures.

**Detection (warning signs):**
- Live metrics significantly worse than offline validation with similar market regime.
- Last-row features change if the same request is repeated within the same candle.
- Unexpectedly high short-term validation scores.

**Phase to address:**
Phase 3 — Temporal Integrity & Data Boundary Enforcement

---

### Pitfall 5: NaN/Inf Propagation From Rolling Indicators

**What goes wrong:**
Rolling/indicator computations create NaN/Inf values; blanket row dropping can remove all rows or unpredictably shrink usable context, causing intermittent inference failures.

**Why it happens:**
- Long lookback windows (e.g., weekly returns) with insufficient history.
- Division-by-zero edge cases in custom volatility-adjusted features.
- No explicit minimum-row policy per feature window.

**Consequences:**
- Intermittent 422/500 errors depending on market data shape.
- Subtle distribution shift when too many rows are dropped and only “easy” rows survive.

**Prevention:**
- Define and enforce `MIN_ROWS_FOR_FEATURES` from **max lookback + safety buffer**.
- Replace/guard Inf and zero-divisions deterministically before final validation.
- Add post-feature quality gate (`no NaN`, `no Inf`, minimum final rows >= 1).
- Emit structured diagnostics for dropped-row counts and offending columns.

**Detection (warning signs):**
- Frequent “All rows contained NaN” or unstable success/failure by pair/time.
- Sudden jump in dropped-row ratio.
- Feature columns with high NaN incidence after upstream schema changes.

**Phase to address:**
Phase 3 — Temporal Integrity & Data Boundary Enforcement

---

### Pitfall 6: Artifact/Code Version Drift (Non-Reproducible Inference)

**What goes wrong:**
Model artifact and serving code evolve independently (different feature logic, library versions, class definitions), causing nondeterministic or incompatible inference behavior.

**Why it happens:**
- Artifact lacks versioned metadata for feature schema and dependency versions.
- Deployment process updates Python/lib versions without compatibility checks.
- No model fingerprint validation at service startup.

**Consequences:**
- Environment-specific bugs (“works in staging, fails in prod”).
- Inconsistent probabilities between nodes/restarts.

**Prevention:**
- Bundle model manifest: model hash, training commit, feature schema hash, dependency versions.
- On startup, validate manifest against runtime expectations; fail closed on mismatch.
- Add deterministic smoke tests in CI/CD using frozen inference fixtures.
- Pin runtime dependency versions for model-serving path.

**Detection (warning signs):**
- Different predictions for same fixture across environments.
- Incident starts after dependency patching, without model change.
- Missing provenance fields in model package.

**Phase to address:**
Phase 2 — Inference Semantics & Output Contract Hardening

---

## Moderate Pitfalls

### Pitfall 1: Upstream OHLCV Shape Irregularities (duplicates, gaps, out-of-order)
**What goes wrong:** malformed market rows contaminate rolling features.
**Prevention:** enforce timestamp monotonicity, deduplicate by timestamp, and reject large gap ratios before feature extraction.

### Pitfall 2: Asset-Specific Logic Leakage
**What goes wrong:** BTC/ETH branching diverges feature behavior unintentionally.
**Prevention:** keep shared feature code path; isolate only truly asset-specific parameters in explicit config.

### Pitfall 3: Over-mocking Tests Hides Real Contract Breaks
**What goes wrong:** tests pass with minimal fake feature frames that never reflect full production schema.
**Prevention:** add contract/integration tests with real feature-column fixtures and strict schema assertions.

## Minor Pitfalls

### Pitfall 1: Ambiguous Error Messages
**What goes wrong:** failures are reported without exact missing/misaligned columns.
**Prevention:** include actionable error payloads (missing columns, unexpected columns, expected order hash).

### Pitfall 2: No Inference Telemetry for Feature Health
**What goes wrong:** silent drift is discovered late.
**Prevention:** log feature checksum, dropped-row count, NaN/Inf count, model/version IDs per request (sampled).

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Contract baseline | Treating docs as contract without executable schema checks | Add manifest + strict pre-predict schema validator |
| Inference hardening | Hardcoded probability index and class assumptions | Resolve target index from class mapping at runtime |
| Temporal/data integrity | Incomplete candles and rolling-window NaN collapse | Closed-candle filter + min-history gate + NaN/Inf validator |
| Testing | Unit tests mock tiny feature sets; misses real mismatches | Add fixture-based end-to-end schema and parity tests |
| Observability | Silent corruption not visible in logs/metrics | Emit contract-check metrics and prediction sanity monitors |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Feature-contract drift | Phase 1 | CI test asserts exact expected columns + order before prediction |
| Validation bypass (`validate_features=False`) | Phase 1 | Static/unit test enforces validation flag and DataFrame input |
| Probability index misinterpretation | Phase 2 | Regression test validates class-label → probability mapping |
| Temporal leakage / incomplete candles | Phase 3 | Time-split leakage tests + repeated intra-candle consistency checks |
| NaN/Inf propagation | Phase 3 | Post-feature gate test fails on any NaN/Inf or zero final rows |
| Artifact/code version drift | Phase 2 | Startup self-check fails on manifest hash/version mismatch |

## Sources

- Project context and requirements: `.planning/PROJECT.md` (HIGH)
- Current implementation and risk surface: `app/features/prediction/service.py` (HIGH)
- Existing tests and coverage gaps: `tests/features/prediction/test_service.py` (HIGH)
- Model contract docs: `app/features/prediction/ml_models/MODEL_USAGE.md`, `OHLCV_PREPROCESS.md` (MEDIUM — internal docs may drift)
- LightGBM Python API (`predict`, `predict_proba`, `validate_features`):
  - https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.LGBMClassifier.html (HIGH)
  - https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.Booster.html (HIGH)
- LightGBM prediction parameters (`predict_disable_shape_check` caution):
  - https://lightgbm.readthedocs.io/en/stable/Parameters.html (HIGH)
- scikit-learn common pitfalls (inconsistent preprocessing, leakage, pipeline discipline):
  - https://scikit-learn.org/stable/common_pitfalls.html (HIGH)
- pandas reindex behavior for enforcing column order:
  - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.reindex.html (HIGH)
