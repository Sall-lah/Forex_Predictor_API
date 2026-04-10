# Project Research Summary

**Project:** Forex Predictor API
**Domain:** FastAPI backend migration to `apps/api` + placeholder `apps/web` monorepo
**Researched:** 2026-04-11
**Confidence:** HIGH

## Executive Summary

This project is a backend-first product (live FX data + prediction API) undergoing a structural migration to a monorepo layout with independent `api` and `web` app boundaries. The research is consistent across stack, features, architecture, and pitfalls: experts treat this as a **move-for-isolation and operability**, not a rewrite. The recommended implementation is to preserve backend behavior first, keep web intentionally minimal, and only then add orchestration enhancements.

The strongest approach is: move current FastAPI code into `apps/api` with parity tests, enforce app-local env ownership (`apps/api/.env`, `apps/web/.env.local`), and establish canonical per-app run/test commands before introducing optional tooling complexity. Stack guidance points to modern reproducible tooling (uv + lockfile for Python, pnpm + optional turbo for workspace orchestration), while architecture guidance emphasizes app-owned runtime boundaries and explicit contract-based integration (web talks to API over HTTP only).

Primary risks are operational, not algorithmic: import/path drift after folder moves, environment leakage across app boundaries, and CI silently running stale paths or partial tests. Mitigation is phase-gated migration with parity checks, explicit working directories, test collection assertions, and strict anti-scope rules (no full web build in this milestone).

## Key Findings

### Recommended Stack

Research converges on keeping the current Python/FastAPI core and modernizing package/task management around monorepo boundaries. The key requirement is reproducibility and independent runtime ownership per app, not introducing novel infrastructure.

**Core technologies:**
- **FastAPI 0.135.3 + Pydantic 2.12.5:** API contracts and validation — aligns with current ecosystem standard and existing code shape.
- **uv 0.11.6:** Python dependency/project management — single-source lockfile workflow (`pyproject.toml` + `uv.lock`) reduces drift.
- **pnpm 10.33.0:** workspace package management — strict dependency boundaries and reliable root orchestration.
- **Turborepo 2.9.6 (optional early, useful soon):** filtered, cacheable cross-app task execution — improves CI/local speed as repo grows.
- **Vite 8.0.8 (web placeholder):** minimal independently runnable frontend shell without committing to full frontend scope.

**Critical version requirements:**
- Node.js **20.19+** for Vite 8 compatibility.
- FastAPI version line compatible with Pydantic v2.
- Use locked Python dependency workflow (`uv lock`, frozen CI installs).

### Expected Features

Feature research is clear: v1 is about safe monorepo operability and zero regression in API behavior.

**Must have (table stakes):**
- Independent `api` and `web` execution paths.
- App-local environment config and validation.
- Backend behavior parity after relocation.
- Root command surface with scoped task execution.
- CI scoping so API and web checks run independently.
- Migration/onboarding docs that reflect new paths and commands.

**Should have (competitive):**
- Graph-aware affected execution.
- Remote task cache.
- Contract-first API artifact flow for future web consumption.
- Optional one-command full-stack dev profile.

**Defer (v2+):**
- Generators/scaffolding for future packages.
- Rich API-to-web typed SDK automation pipeline.
- Any non-placeholder web product implementation.

### Architecture Approach

Architecture guidance recommends a strict app boundary model under `apps/`: `apps/api` owns backend runtime/deps/tests/config; `apps/web` owns frontend runtime/config; repo root only orchestrates tasks and docs. Communication is explicit over HTTP contracts (no cross-app imports, no shared runtime env files). Migration order should be “move-as-is, validate parity, isolate config, then optimize orchestration and harden contracts.”

**Major components:**
1. **`apps/api`** — existing FastAPI layered backend + tests + model artifact configuration.
2. **`apps/web`** — minimal placeholder app with independent run and env contract.
3. **Repo root orchestration** — workspace commands, optional turbo pipelines, CI entrypoints, migration docs.
4. **Cross-app contract layer** — explicit base URL/CORS/env contract (public values only).

### Critical Pitfalls

1. **Import/path drift after move** — prevent with canonical `api` root command contract and parity smoke runs from both root and app context.
2. **Cross-app env leakage** — prevent with app-local env files only and explicit precedence validation.
3. **CI old-path assumptions** — prevent with explicit job working directories, split app jobs, and temporary stale-path checks.
4. **Pytest discovery drift** — prevent with pinned invocation paths/config and collected-test-count guardrails.
5. **Command sprawl** — prevent with one canonical command set per app (dev/test/run) reused in docs + CI.

## Implications for Roadmap

Based on combined research, suggested phase structure:

### Phase 1: Boundary Migration + Parity Lock
**Rationale:** Highest dependency and risk concentration; everything else depends on stable app boundaries.
**Delivers:** `apps/api` + `apps/web` structure, backend relocated with unchanged API behavior, placeholder web runnable.
**Addresses:** Independent app execution, backend parity, anti-feature guardrail against full web scope.
**Avoids:** Import/path drift, hidden shared-state coupling, over-scaffolding web.

### Phase 2: Runtime Contract + Env Isolation
**Rationale:** Independent operation is unreliable without strict config ownership and canonical commands.
**Delivers:** Per-app env contracts (`.env.example`), startup validation, canonical dev/test/run commands per app.
**Addresses:** App-local env config, root command ergonomics, onboarding clarity.
**Avoids:** Cross-app env leakage, command sprawl, “works only from folder X” failures.

### Phase 3: CI/Task Orchestration Split
**Rationale:** Once local parity is stable, CI must mirror app boundaries to prevent false greens/reds.
**Delivers:** API/web split CI jobs, explicit working directories, scoped task execution (`--filter` / app-targeted commands), test count assertions.
**Addresses:** CI path scoping table-stake, scoped execution requirement.
**Avoids:** Stale root assumptions, skipped tests, pytest rootdir drift.

### Phase 4: Contract Hardening + Scaling Enhancements
**Rationale:** Add leverage only after correctness and operability are established.
**Delivers:** API↔web contract hardening (base URL/CORS/OpenAPI artifact), optional graph-aware affected runs, optional remote caching.
**Uses:** Turborepo/pnpm capabilities and architecture contract patterns.
**Implements:** Differentiators without destabilizing baseline migration.

### Phase Ordering Rationale

- Structural correctness before tooling optimization minimizes regression blast radius.
- Architecture boundaries (app-owned runtime/config) map directly to phase boundaries.
- Pitfall-heavy items (imports/env/CI/test discovery) are front-loaded to reduce downstream rework.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** choose and calibrate orchestration strategy (plain pnpm filters vs turbo pipelines vs later Nx-style affected).
- **Phase 4:** API contract artifact strategy (OpenAPI generation/validation flow and when to introduce typed client generation).
- **Deployment hardening work in/after Phase 4:** container/runtime env precedence behavior across environments.

Phases with standard patterns (likely skip `/gsd-research-phase`):
- **Phase 1:** folder migration + parity workflow is well-documented and already tightly specified.
- **Phase 2:** app-local env ownership and canonical command contracts are mature, standard practices.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Strong primary sources (Context7 + official docs) with explicit versions and compatibility constraints. |
| Features | HIGH | Clear project-aligned priorities with direct dependency mapping and anti-feature clarity. |
| Architecture | HIGH | Patterns are conservative, standard, and consistent with existing backend layering. |
| Pitfalls | MEDIUM-HIGH | High-quality docs-backed pitfalls; some CI/deployment behaviors still environment-specific and require local validation. |

**Overall confidence:** HIGH

### Gaps to Address

- **Tooling finalization gap (turbo optionality):** Decide whether to adopt turbo immediately or start with pnpm-only filtering and defer orchestration complexity.
- **Python dependency migration gap:** Existing repo uses `requirements.txt` + `environment.yml`; research recommends uv lockfile flow, so migration approach needs an explicit transition plan.
- **Contract automation depth gap:** Define how far to go in v1 (artifact only vs enforced consumer validation).
- **CI baseline metrics gap:** Establish expected test collection and runtime thresholds before/after migration for objective parity checks.

## Sources

### Primary (HIGH confidence)
- Context7 `/fastapi/fastapi` — FastAPI patterns, deployment guidance, deprecations.
- Context7 `/astral-sh/uv` — lock/sync workflow and project management patterns.
- Context7 `/pydantic/pydantic-settings` — env file behavior and configuration patterns.
- Official docs: pnpm workspaces/filtering, Turborepo task running/caching, Nx affected/caching docs.
- Python/Pytest/Uvicorn/GitHub Actions official docs for path resolution, test discovery, runtime and CI working-directory behavior.

### Secondary (MEDIUM confidence)
- PyPI/npm registry version checks for package currency and compatibility planning.

### Tertiary (LOW confidence)
- None material; low-confidence claims were not required for roadmap-level decisions.

---
*Research completed: 2026-04-11*
*Ready for roadmap: yes*
