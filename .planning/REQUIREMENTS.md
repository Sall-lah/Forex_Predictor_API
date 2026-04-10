# Requirements: Forex Predictor API - Prediction Alignment Update

**Defined:** 2026-04-09
**Core Value:** Prediction requests must reliably produce model-valid outputs using the exact expected feature contract.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Prediction Core

- [x] **PRED-01**: Prediction service generates features using a deterministic extraction path aligned with `app/features/prediction/ml_models/OHLCV_PREPROCESS.md`.
- [x] **PRED-02**: Prediction service resolves and validates model file path handling so inference loads the intended model artifact reliably.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

(None)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Model retraining/replacement | Keep scope focused on runtime alignment fixes only |
| New endpoints/API contract redesign | Avoid client-facing surface changes in this milestone |
| UI/client updates | Backend prediction reliability is the only target |
| Infrastructure/deployment changes | No platform work needed for this reliability slice |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRED-01 | Phase 1 (Prediction Contract Alignment) | Complete |
| PRED-02 | Phase 1 (Prediction Contract Alignment) | Complete |

**Coverage:**
- v1 requirements: 2 total
- Mapped to phases: 2
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-09*
*Last updated: 2026-04-09 after roadmap creation*
