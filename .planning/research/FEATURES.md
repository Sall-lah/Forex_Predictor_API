# Feature Research

**Domain:** API + web monorepo restructuring (web placeholder initially)
**Researched:** 2026-04-11
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Independent app execution (`api` and `web`) | Core promise of monorepo split is separate run workflows | MEDIUM | Must support `api` boot without `web`, and `web` placeholder boot without `api` runtime coupling |
| App-local environment configuration (`api/.env`, `web/.env`) | Prevents config leakage and accidental cross-app breakage | MEDIUM | Keep env schema validation app-specific; avoid root-global env file as default |
| Backend behavior parity after move | Existing consumers expect no endpoint regressions from restructuring | HIGH | Migration is structural, not product rewrite; require existing API tests to pass in `api/` path |
| Root-level developer commands for common workflows | Teams expect one entrypoint for install/lint/test/dev across apps | LOW | Use workspace runner scripts at root; delegate to app-specific commands |
| Scoped task execution (run only one app or changed app) | Monorepos become slow/noisy without filtering | MEDIUM | pnpm `--filter`, Turborepo `--filter`, Nx `affected` are standard patterns |
| CI path/affected scoping between `api` and `web` | Placeholder web should not block API delivery and vice versa | MEDIUM | At minimum, path-based CI split; ideally graph/affected execution |
| Monorepo onboarding docs | Repo structure shift requires explicit local workflow guidance | LOW | Document commands, env locations, and "web is placeholder" constraints |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Graph-aware affected pipelines (not just path filters) | Much faster CI on large repo growth; scales beyond two apps | MEDIUM | Nx affected or equivalent graph-based tooling gives better precision than simple folder matching |
| Shared remote task cache (local + CI) | Major developer speed-up on repeated lint/test/build tasks | MEDIUM | Turborepo/Nx both support remote caching patterns; high payoff as repo grows |
| Contract-first API artifact flow to web placeholder | De-risks future frontend by validating API contract from day one | MEDIUM | Generate OpenAPI artifact in `api`, make `web` consume or validate against it even as placeholder |
| One-command full-stack dev profile | Better DX for new contributors while preserving independent runtimes | MEDIUM | Keep separate app commands plus optional composed command (e.g., run both concurrently) |
| Scaffold/generator workflow for future apps/packages | Prevents repo drift and enforces structure conventions | HIGH | Useful once monorepo expands beyond `api`/`web`; can be deferred until after baseline migration |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Build full web app in restructure milestone | "We already have `web/`, let’s start shipping UI now" | Violates migration scope, increases risk to API parity, delays core restructure value | Keep `web/` as executable placeholder with health route/skeleton only |
| Premature shared "common" package extraction | "DRY everything immediately" | Creates unstable abstractions before real cross-app usage patterns exist | Duplicate small pieces initially; extract only after repeated, proven reuse |
| Multiple orchestrators at once (Nx + Turborepo + custom scripts) | "Future-proof tooling" mindset | Tool overlap, config churn, unclear ownership, slower onboarding | Pick one orchestration path and keep root scripts stable |
| Tight runtime coupling between placeholder web and API startup | "Single command should fail if either app is missing" | Prevents independent operation goal and blocks placeholder progress | Support optional composed run, but preserve standalone app boot |

## Feature Dependencies

```
[Independent app execution]
    └──requires──> [App-local env configuration]
                          └──requires──> [Monorepo onboarding docs]

[Backend behavior parity after move]
    └──requires──> [Scoped task execution]
                          └──requires──> [CI path/affected scoping]

[Contract-first API artifact flow to web placeholder]
    └──requires──> [Independent app execution]
    └──enhances──> [Future web implementation readiness]

[One-command full-stack dev profile] ──enhances──> [Independent app execution]

[Build full web app in restructure milestone] ──conflicts──> [Backend behavior parity after move]
```

### Dependency Notes

- **Independent app execution requires app-local env configuration:** each app needs isolated runtime contracts to avoid accidental cross-loading of environment values.
- **Backend behavior parity requires scoped task execution:** migration validation is only reliable when API tests/lint can be run in isolation and in CI.
- **Scoped task execution requires CI path/affected scoping:** local filtering without CI filtering still causes noisy and slow pipelines.
- **Contract-first API artifact flow requires independent app execution:** the contract producer (`api`) and consumer (`web`) must be decoupled to avoid lockstep runtime dependencies.
- **Full web implementation conflicts with parity-first restructure:** adding product scope during structural migration creates mixed acceptance criteria and delays stability.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Independent `api` and `web` run workflows — core milestone promise
- [ ] App-local env file conventions and validation — required for runtime isolation
- [ ] API parity verification after relocation to `api/` — preserves current product value
- [ ] Root command surface + scoped execution (`api` only / `web` only) — required developer ergonomics
- [ ] CI split for `api` vs `web` changes — prevents placeholder web from slowing API evolution

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Graph-aware affected execution — add when CI runtime starts increasing
- [ ] Remote task caching — add when team/CI repetition cost is visible
- [ ] Optional composed full-stack run command — add once both apps have active dev loops

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] App/package generators for scaled monorepo governance — defer until new packages are frequent
- [ ] Rich API-to-web contract automation (typed SDK generation in CI) — defer until web implementation begins

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Independent app execution | HIGH | MEDIUM | P1 |
| App-local env configuration | HIGH | MEDIUM | P1 |
| API parity verification post-move | HIGH | HIGH | P1 |
| Root command surface + scoped tasks | HIGH | LOW | P1 |
| CI path/affected scoping | HIGH | MEDIUM | P1 |
| Graph-aware affected pipelines | MEDIUM | MEDIUM | P2 |
| Remote task cache | MEDIUM | MEDIUM | P2 |
| Contract-first API artifact flow | MEDIUM | MEDIUM | P2 |
| Scaffolding generators | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Turborepo-style workflow | Nx-style workflow | Our Approach |
|---------|--------------------------|-------------------|--------------|
| Scoped execution | `--filter` package/directory/change filters | `affected` + project graph | Start with simple path/package filters; evolve to graph-aware once needed |
| Task acceleration | Local + remote cache via task hashing | Local + remote cache + affected integration | Add caching after baseline restructure is stable |
| Task orchestration | Root `turbo run` scripts and pipeline config | Targets/pipelines in `nx.json` + `run-many` | Keep root commands stable and tooling-agnostic during initial migration |

## Sources

- Project scope and constraints: `.planning/PROJECT.md` (HIGH confidence, project-primary source)
- pnpm workspace docs (workspace structure, release workflow, config): https://pnpm.io/workspaces (Last updated Mar 30, 2026) (HIGH confidence)
- pnpm filtering docs (`--filter`, changed-since, scoped execution): https://pnpm.io/filtering (Last updated Mar 30, 2026) (HIGH confidence)
- Turborepo running tasks docs (`turbo run`, filtering, automatic package scoping): https://turbo.build/repo/docs/crafting-your-repository/running-tasks (HIGH confidence)
- Turborepo caching docs (local/remote cache behavior, hash inputs/outputs): https://turbo.build/repo/docs/core-concepts/caching (HIGH confidence)
- Nx affected docs (`nx affected`, CI base/head strategy): https://nx.dev/docs/features/ci-features/affected (HIGH confidence)
- Nx run tasks docs (run-many, pipelines, parallel execution): https://nx.dev/docs/features/run-tasks (HIGH confidence)
- Nx cache task results docs (cacheable targets, remote cache): https://nx.dev/docs/features/cache-task-results (HIGH confidence)

---
*Feature research for: API+web monorepo restructure with independent app execution*
*Researched: 2026-04-11*
