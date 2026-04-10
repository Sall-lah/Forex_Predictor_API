# Roadmap: Forex Predictor API - Prediction Alignment Update

## Overview

This roadmap delivers one focused reliability milestone: prediction requests must either produce model-valid outputs using the documented feature contract or fail with clear, actionable errors. The phase is organized as a complete vertical capability so API consumers can trust prediction behavior without API-surface changes.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Prediction Contract Alignment** - Align preprocessing and model-input validation so predictions are reliable and contract-safe.

## Phase Details

### Phase 1: Prediction Contract Alignment
**Goal**: API consumers can request predictions that are generated only from correctly aligned preprocessing/model inputs, with clear failure responses when alignment is invalid.
**Depends on**: Nothing (first phase)
**Requirements**: PRED-01, PRED-02
**Success Criteria** (what must be TRUE):
  1. API consumer can call the prediction endpoint with valid inputs and receive a successful prediction response produced from the documented preprocessing feature set.
  2. Equivalent valid prediction requests produce the same required feature column set/order expected by the documented preprocessing contract.
  3. Prediction requests consistently load and use the intended model artifact path, and misconfigured/unavailable model paths fail with an explicit load/availability error instead of silent or ambiguous failures.
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Enforce deterministic feature-contract alignment before prediction inference.
- [x] 01-02-PLAN.md — Unify prediction response schema/router contract with `probability_up` output.
- [x] 01-03-PLAN.md — Harden model artifact path resolution and load-failure reliability.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 1.1 → 1.2 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Prediction Contract Alignment | 0/3 | Not started | - |
