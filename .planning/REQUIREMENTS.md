# Requirements: Forex Predictor API Monorepo Restructure

**Defined:** 2026-04-11
**Core Value:** Both applications can run independently with isolated environment configuration, while preserving current API functionality during the migration.

## v1 Requirements

Requirements for initial migration release. Each maps to exactly one roadmap phase.

### Repository Structure

- [x] **STRU-01**: Developer can see a repository layout with separate top-level application directories for backend and frontend (`api/` and `web/`).
- [x] **STRU-02**: Existing backend service code, tests, and runtime assets are migrated into `api/` with clear app-local ownership.
- [ ] **STRU-03**: Developer can start `web/` as a runnable placeholder app without frontend feature implementation.

### Runtime and Environment Isolation

- [ ] **ENV-01**: Developer can configure backend runtime using `api/.env` (and `api/.env.example`) without depending on root-level `.env` values.
- [ ] **ENV-02**: Developer can configure frontend placeholder runtime using `web/.env` or `web/.env.local` (with example file) independently from backend env values.
- [ ] **ENV-03**: Developer gets app-specific configuration validation so invalid/missing env values fail clearly in the relevant app.

### Independent Execution and Parity

- [ ] **EXEC-01**: Developer can run backend app independently from `api/` using canonical commands documented for local development.
- [ ] **EXEC-02**: Developer can run frontend placeholder independently from `web/` using canonical commands documented for local development.
- [x] **PAR-01**: Existing backend API endpoints preserve behavior parity after migration to `api/`.

### Developer Workflow and CI

- [ ] **WORK-01**: Developer can run root-level convenience commands that delegate to app-scoped commands without coupling app runtimes.
- [ ] **WORK-02**: Developer can run scoped tasks for only one app (`api` or `web`) during lint/test/dev workflows.
- [ ] **CI-01**: CI can evaluate backend and frontend placeholder through app-scoped execution paths (path- or target-scoped), so web placeholder changes do not block unrelated backend checks.

### Documentation and Onboarding

- [ ] **DOCS-01**: Developer can follow updated onboarding/run docs that describe the new monorepo structure and independent app commands.

## v2 Requirements

Deferred until migration baseline is stable.

### Monorepo Enhancements

- **MREP-01**: Developer can use affected-graph task execution for faster CI and local runs.
- **MREP-02**: Developer can use remote task caching for lint/test/build workflows.
- **MREP-03**: Frontend can consume an automated API contract artifact pipeline (OpenAPI-to-client workflow).

## Out of Scope

Explicitly excluded from this initialization scope.

| Feature | Reason |
|---------|--------|
| Full frontend feature implementation in `web/` | Current scope is structural migration and placeholder setup only. |
| Prediction-model redesign or retraining changes | Request focuses on folder/runtime restructuring, not ML capability changes. |
| Breaking API contract changes during migration | Migration goal is parity, not product-level API redesign. |
| Multi-orchestrator tooling rollout in one milestone | Adds complexity and migration risk before baseline structure is stable. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| STRU-01 | Phase 1 | Complete |
| STRU-02 | Phase 1 | Complete |
| STRU-03 | Phase 1 | Pending |
| ENV-01 | Phase 2 | Pending |
| ENV-02 | Phase 2 | Pending |
| ENV-03 | Phase 2 | Pending |
| EXEC-01 | Phase 2 | Pending |
| EXEC-02 | Phase 2 | Pending |
| PAR-01 | Phase 1 | Complete |
| WORK-01 | Phase 3 | Pending |
| WORK-02 | Phase 3 | Pending |
| CI-01 | Phase 3 | Pending |
| DOCS-01 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-11*
*Last updated: 2026-04-11 after initial definition*
