# Project Research Summary

**Project:** Forex Predictor API
**Domain:** Production ML inference reliability for forex/crypto prediction (FastAPI + LightGBM)
**Researched:** 2026-04-09
**Confidence:** HIGH

## Executive Summary

This project is a reliability-hardening effort for a FastAPI-based market prediction API, not a greenfield model build. The research converges on one dominant pattern used by mature ML inference systems: treat inference as a strict contract problem. That means shipping model + feature schema + preprocessing manifest together, enforcing exact feature names/order/dtypes before inference, and failing closed when alignment checks fail.

The recommended approach is to keep the current Python/FastAPI/LightGBM stack, but harden operational guarantees around it: deterministic preprocessing, contract validation gates, explicit class-probability semantics, domain-specific error taxonomy, and baseline telemetry. This gives the fastest path to materially safer predictions without disruptive model-platform migration.

The highest risks are silent prediction corruption (feature-order drift, disabled validation, class-index assumptions), temporal leakage from incomplete candles, and artifact/runtime version drift. Mitigation is clear: enforce executable manifests at startup and pre-predict, keep LightGBM feature validation enabled, codify class mapping in metadata, add parity/regression tests in CI, and instrument reason-coded failures for rapid detection.

## Key Findings

### Recommended Stack

Research strongly supports staying on the current architecture baseline (Python 3.12 + FastAPI + LightGBM) and focusing on strict contract enforcement and reproducibility. The stack guidance is modern and source-backed (FastAPI lifespan pattern, strict Pydantic v2 validation, pinned dependency strategy, and LightGBM safety checks).

**Core technologies:**
- **Python 3.12.x**: serving runtime — aligns with current repo and stable scientific/ML ecosystem compatibility.
- **FastAPI 0.135.3**: API lifecycle and DI — use `lifespan` for model bundle init/cleanup.
- **Uvicorn 0.44.0**: ASGI serving — explicit production controls for concurrency/timeouts/proxy trust.
- **Pydantic 2.12.5**: strict request/response validation — enforce fail-closed contracts (`extra='forbid'`, strict mode).
- **pandas 3.0.2 + numpy 2.4.4**: deterministic feature engineering and numeric substrate.
- **scikit-learn 1.8.0**: pipeline/contract discipline and model-compatibility metadata conventions.
- **LightGBM 4.6.0**: inference engine — keep feature/shape validation enabled.

Critical version implication: pin model-serving dependencies with lockfiles and store artifact/runtime compatibility metadata together to prevent environment drift.

### Expected Features

**Must have (table stakes):**
- Strict inference schema enforcement (exact feature names, order, dtypes).
- Pre-inference completeness and NaN/Inf guardrails.
- Stable confidence output contract (class probabilities + class mapping).
- Actionable failure taxonomy (clear 422/502/503 semantics, structured payloads).
- Baseline observability (request IDs, structured logs, latency/error metrics).
- Contract regression tests in CI for train/serve alignment.

**Should have (competitive):**
- Prediction provenance envelope (model version, schema hash, time window).
- Reliability reason-code dashboard for ops/MTTR.

**Defer (v2+):**
- Probability calibration workflow + calibration metadata lifecycle.
- Policy-driven degraded mode/fallback beyond strict fail-closed defaults.

### Architecture Approach

The architecture recommendation is layered and explicit: thin router → orchestration service → deterministic preprocessing pipeline → feature contract guard → model compatibility guard → strict inference wrapper → explicit fallback policy → response mapper with telemetry. The most important structural rule is to deploy a **model bundle** (model artifact + feature contract + preprocessing manifest) as one atomic unit.

**Major components:**
1. **Prediction Orchestrator** — enforces request flow and guard ordering.
2. **Preprocess Pipeline** — deterministic feature generation only.
3. **Contract + Compatibility Guards** — required/order/dtype/null checks plus model compatibility checks before predict.
4. **Inference Engine** — thin, strict `predict_proba` wrapper with validation on.
5. **Fallback Policy Engine** — explicit `PRIMARY/FALLBACK/FAIL_CLOSED` decisioning.
6. **Telemetry Layer** — reason-coded logs/metrics for every guard/fallback branch.

### Critical Pitfalls

1. **Feature-contract drift** — prevent via executable manifest, strict pre-predict alignment gate, and CI contract tests.
2. **Validation bypass (`validate_features=False` / ndarray path)** — prevent by requiring DataFrame named columns and enforced validation flag in code/tests.
3. **Probability mislabeling from class-index assumptions** — prevent by persisting/verifying class mapping and deriving indexes dynamically.
4. **Temporal leakage / incomplete candle contamination** — prevent via closed-candle filters and parity tests with training-time window logic.
5. **Artifact/code version drift** — prevent via startup manifest hash/version checks and pinned dependency locks.

## Implications for Roadmap

Based on combined research, the roadmap should prioritize **contract integrity first**, then **inference semantics hardening**, then **temporal/data integrity**, followed by **operability enhancements**.

### Phase 1: Contract Foundation & Schema Gate
**Rationale:** Every downstream reliability control depends on canonical feature/schema truth.
**Delivers:** `feature_contract.json` + `preprocess_manifest.json`, startup model-bundle validation, `validate_and_align()` gate (required/order/dtype/null checks), strict DataFrame inference path.
**Addresses:** P1 features (strict schema enforcement, failure clarity baseline, contract tests).
**Avoids:** Pitfalls 1 and 2 (contract drift, validation bypass).

### Phase 2: Inference Semantics & Error Contract Hardening
**Rationale:** Once schema safety exists, output semantics and runtime compatibility can be made trustworthy.
**Delivers:** class-mapping metadata verification, stable probability response contract, domain error taxonomy (`code/detail/action/request_id`), compatibility guardrails, artifact-version self-check.
**Addresses:** P1 features (confidence contract, actionable failures) + part of P2 provenance groundwork.
**Avoids:** Pitfalls 3 and 6 (probability misinterpretation, artifact/version drift).

### Phase 3: Temporal Integrity & Feature Quality Enforcement
**Rationale:** Preventing leakage and NaN/Inf collapse requires dedicated data-boundary enforcement after core contract controls.
**Delivers:** closed-candle policy, min-history gates, deterministic rolling-window parity checks, NaN/Inf quality gates, fixture-based parity tests.
**Addresses:** P1 reliability completeness.
**Avoids:** Pitfalls 4 and 5 (temporal leakage, NaN/Inf propagation).

### Phase 4: Observability & Reliability Operations
**Rationale:** After correctness controls are in place, instrument the system to detect and triage issues quickly.
**Delivers:** structured telemetry for guard/fallback decisions, reason-coded metrics, latency/error dashboards, request-id traceability.
**Addresses:** P1 observability + P2 reason-code dashboard.
**Avoids:** silent corruption and slow incident detection.

### Phase 5: Controlled Enhancements (v1.x → v2)
**Rationale:** Add complexity only after baseline reliability is proven in production.
**Delivers:** provenance envelope, optional fallback/degraded policy engine, calibration workflow.
**Addresses:** P2/P3 differentiators.
**Avoids:** premature complexity that masks baseline contract issues.

### Phase Ordering Rationale

- Contract and deterministic preprocessing must precede any fallback or advanced confidence features.
- Semantic correctness (class mapping/output contract) should be hardened before adding dashboards and richer metadata.
- Temporal integrity is separated explicitly because it requires dedicated parity/leakage testing discipline.
- Operability comes after correctness to avoid instrumenting unstable behaviors.

### Research Flags

Phases likely needing deeper `/gsd-research-phase` support:
- **Phase 3 (Temporal Integrity):** leakage testing strategy and candle-closure edge cases are domain-sensitive.
- **Phase 5 (Calibration / Degraded Mode):** calibration methodology, SLA/risk policy, and fallback governance need explicit product decisions.

Phases with standard patterns (can likely skip deep research):
- **Phase 1 (Contract Foundation):** strongly documented patterns across FastAPI/Pydantic/LightGBM/sklearn.
- **Phase 2 (Error + Semantics Hardening):** mostly implementation discipline over novel research.
- **Phase 4 (Baseline Observability):** established OTel/Prometheus patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Strongly grounded in official docs + repo compatibility; versions/rationale explicit. |
| Features | MEDIUM-HIGH | Clear prioritization and dependencies; some differentiators (calibration/degraded mode) remain policy-dependent. |
| Architecture | HIGH | Cohesive layered design with clear boundaries and build-order implications. |
| Pitfalls | HIGH | Failure modes are concrete, phase-mapped, and paired with testable mitigations. |

**Overall confidence:** HIGH

### Gaps to Address

- **Canonical manifest ownership/governance:** define who updates feature contract + preprocessing manifest and release gating rules.
- **Calibration readiness criteria:** define data volume/quality and monitoring thresholds required before enabling calibrated probabilities.
- **Fallback risk policy:** explicitly decide fail-closed vs fallback behavior per failure class before implementing degraded mode.
- **`ta` dependency longevity:** maintain regression tests around indicator outputs; decide later whether to replace with fully in-house formulas.

## Sources

### Primary (HIGH confidence)
- `.planning/research/STACK.md` — validated stack/version strategy and contract-first implementation approach.
- `.planning/research/FEATURES.md` — MVP/P1 reliability features, dependencies, and anti-features.
- `.planning/research/ARCHITECTURE.md` — layered target architecture, patterns, and phase boundaries.
- `.planning/research/PITFALLS.md` — phase-mapped reliability failure modes and prevention controls.
- Context7 + official docs cited in source research:
  - `/fastapi/fastapi`, `/kludex/uvicorn`, `/pydantic/pydantic`
  - `/scikit-learn/scikit-learn`, `/lightgbm-org/lightgbm`, `/pandas-dev/pandas`
  - FastAPI, LightGBM, scikit-learn, pandas official documentation URLs referenced in research files.

### Secondary (MEDIUM confidence)
- Internal model/preprocess docs: `app/features/prediction/ml_models/MODEL_USAGE.md`, `OHLCV_PREPROCESS.md` (authoritative for current repo but can drift without executable manifests).
- `/open-telemetry/opentelemetry-python`, `/prometheus/client_python` patterns for production telemetry implementation.

### Tertiary (LOW confidence)
- None identified as primary decision drivers; no major roadmap recommendation relies on low-confidence sources.

---
*Research completed: 2026-04-09*
*Ready for roadmap: yes*
