# Roadmap: Forex Predictor API Monorepo Restructure

## Overview

This roadmap delivers a safe monorepo migration in three coarse phases: first establish new app boundaries without backend regressions, then enforce app-local runtime isolation with independent execution, and finally complete root workflow, CI scoping, and onboarding documentation so daily development works cleanly across both apps.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: App Boundary Migration & Backend Parity** - Restructure into `api/` + `web/` placeholder while preserving API behavior. (completed 2026-04-12)
- [ ] **Phase 2: Runtime Isolation & Independent App Execution** - Make each app self-contained for env configuration and local startup.
- [ ] **Phase 3: Monorepo Workflow, CI Scoping & Onboarding Docs** - Finalize root/scoped workflows and documentation for reliable day-to-day use.

## Phase Details

### Phase 1: App Boundary Migration & Backend Parity
**Goal**: Developers can work in a monorepo layout with clear `api/` and `web/` app boundaries while existing backend API behavior remains unchanged after migration.
**Depends on**: Nothing (first phase)
**Requirements**: STRU-01, STRU-02, STRU-03, PAR-01
**Success Criteria** (what must be TRUE):
  1. Developer can see and navigate a top-level repo layout that separates backend and frontend app directories (`api/` and `web/`).
  2. Backend source code, tests, and runtime assets are owned under `api/` and no longer require root-level app paths.
  3. Developer can start `web/` as a runnable placeholder application.
  4. Existing backend endpoints return parity-equivalent responses after the move to `api/`.
**Plans**: TBD

### Phase 2: Runtime Isolation & Independent App Execution
**Goal**: Developers can configure and run each app independently with app-local environment contracts and clear validation failures.
**Depends on**: Phase 1
**Requirements**: ENV-01, ENV-02, ENV-03, EXEC-01, EXEC-02
**Success Criteria** (what must be TRUE):
  1. Developer can configure backend runtime using `api/.env` (with `api/.env.example`) without relying on root-level `.env` values.
  2. Developer can configure web placeholder runtime using `web/.env` or `web/.env.local` (with example file) independently from backend values.
  3. Invalid or missing app configuration fails with clear, app-specific validation errors.
  4. Developer can run backend independently from `api/` using canonical local development commands.
  5. Developer can run web placeholder independently from `web/` using canonical local development commands.
**Plans**: TBD

### Phase 3: Monorepo Workflow, CI Scoping & Onboarding Docs
**Goal**: Developers and CI can execute root-level and app-scoped workflows reliably, with onboarding docs that match the new monorepo operating model.
**Depends on**: Phase 2
**Requirements**: WORK-01, WORK-02, CI-01, DOCS-01
**Success Criteria** (what must be TRUE):
  1. Developer can run root-level convenience commands that delegate to app-scoped commands without coupling app runtimes.
  2. Developer can run lint/test/dev tasks for only one selected app (`api` or `web`).
  3. CI executes backend and web placeholder checks through app-scoped paths so unrelated app changes do not block each other.
  4. A new developer can follow onboarding docs to understand structure and run both apps with the documented independent command flow.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 1.1 → 2 → 2.1 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. App Boundary Migration & Backend Parity | 2/2 | Complete   | 2026-04-12 |
| 2. Runtime Isolation & Independent App Execution | 0/TBD | Not started | - |
| 3. Monorepo Workflow, CI Scoping & Onboarding Docs | 0/TBD | Not started | - |
