# Domain Pitfalls

**Domain:** Live backend → `api/web` monorepo migration with independent env/runtime paths  
**Researched:** 2026-04-11  
**Confidence:** MEDIUM-HIGH

## Critical Pitfalls

### Pitfall 1: “Moved folders, broke imports” (Python module path drift)
**What goes wrong:**  
After moving backend code under `api/`, import resolution changes (`ModuleNotFoundError`, wrong package roots, flaky local vs CI behavior).

**Why it happens:**  
Teams assume repo-root execution semantics still apply. Python import path depends on execution context and script location.

**Consequences:**  
API boots locally for one developer but fails in CI/containers; tests fail depending on current working directory.

**Prevention strategy:**  
- Treat `api/` as the Python project root and standardize all commands from that root.
- Use explicit launch conventions (e.g., `uvicorn app.main:app --app-dir api` from repo root, or run from `api/` directly).
- Add a migration gate: run startup and tests both from repo root and from `api/` to catch path assumptions.

**Warning signs:**
- `ModuleNotFoundError` after directory move.
- Different behavior between `pytest` run from root vs `api/`.
- Uvicorn starts only with ad-hoc `PYTHONPATH` tweaks.

**Phase mapping:**  
**Phase 1 (Restructure + boot safety):** finalize import strategy and run-command contract before any new feature work.

---

### Pitfall 2: Cross-app env leakage (`.env` scope confusion)
**What goes wrong:**  
`api` and `web` read each other’s variables, or root-level `.env` accidentally overrides app-local values.

**Why it happens:**  
Dotenv and tooling precedence rules are often misunderstood. Teams keep a root `.env` “temporarily” and never remove ambiguity.

**Consequences:**  
Wrong runtime config in staging/prod, silent credential mix-ups, hard-to-debug “works on my machine” behavior.

**Prevention strategy:**  
- Enforce app-local env files only (`api/.env`, `web/.env`), no shared root runtime `.env`.
- Document and test precedence explicitly (OS env > dotenv for pydantic-settings).
- Add startup validation that logs non-secret config origin/sanity (e.g., expected mode/URL patterns).

**Warning signs:**
- API uses unexpected host/URL without code changes.
- Local and CI config diverge even with same `.env` content.
- Developers export shell vars to “fix” config repeatedly.

**Phase mapping:**  
**Phase 1 (Restructure + config isolation):** define env boundaries and remove ambiguous root-level env behavior.

---

### Pitfall 3: CI still executes from old root assumptions
**What goes wrong:**  
Pipeline scripts continue to run commands in repo root, using stale paths for tests, artifacts, or startup commands.

**Why it happens:**  
Migration updates code tree, but CI defaults/working-directory settings are not migrated in lockstep.

**Consequences:**  
Green local runs but red CI; or worse, CI appears green while skipping the intended app checks.

**Prevention strategy:**  
- Explicitly set `working-directory` for app-specific jobs.
- Split CI into `api` and `web` jobs with independent command contracts.
- Add a temporary parity check job that verifies old paths are no longer referenced.

**Warning signs:**
- CI errors: file not found for old paths.
- Sudden drop in test count after migration.
- Job passes suspiciously fast after major folder move.

**Phase mapping:**  
**Phase 2 (CI/CD migration):** update and validate workflow working directories before declaring migration complete.

---

### Pitfall 4: Test discovery drift after relocating tests/config
**What goes wrong:**  
Pytest rootdir/config selection changes, causing missing tests, different markers/options, or plugin behavior changes.

**Why it happens:**  
Pytest rootdir is derived from invocation paths and nearby config files; moving files without invocation discipline changes behavior.

**Consequences:**  
False confidence from partial test runs, inconsistent node IDs/cache behavior, broken coverage trends.

**Prevention strategy:**  
- Pin test entrypoints (e.g., `pytest api/tests` or run from `api/` consistently).
- Keep one authoritative pytest config location and document it.
- Add CI assertion for expected collected test count threshold.

**Warning signs:**
- `rootdir` in pytest header unexpectedly changes.
- Marker warnings suddenly appear/disappear.
- Coverage drops with no logical code deletion.

**Phase mapping:**  
**Phase 2 (Quality guardrails):** lock test invocation and verify collection parity.

---

### Pitfall 5: Runtime command split without operational contract
**What goes wrong:**  
`api` and `web` have “independent commands” but no canonical scripts, so every engineer/integration runs a different variant.

**Why it happens:**  
Teams stop at folder creation and skip command standardization for local dev, CI, and deployment.

**Consequences:**  
Onboarding friction, flaky reproducibility, and deployment drift (different startup flags/watch dirs/app dirs).

**Prevention strategy:**  
- Define one canonical command set per app (dev, test, prod run).
- Keep command wrappers in-repo (Makefile/scripts/task runner) and use them everywhere.
- Require docs + smoke checks for each command path.

**Warning signs:**
- Team shares one-off commands in chat repeatedly.
- Different run commands in README vs CI vs deployment manifests.
- “It only works when I run it from X folder.”

**Phase mapping:**  
**Phase 1 (Developer experience contract):** establish canonical commands before structural migration is considered done.

## Moderate Pitfalls

### Pitfall 1: Hidden shared-state coupling
**What goes wrong:**  
Code assumes shared root files/paths (model artifacts, temp dirs, caches) that break once app boundaries are isolated.

**Prevention:**  
Inventory filesystem dependencies; convert to app-scoped paths/config with explicit defaults.

**Warning signs:**
- Runtime errors for missing relative files after move.
- Artifact path fixes hardcoded in multiple places.

**Phase mapping:**  
**Phase 1:** dependency/path audit during move.

### Pitfall 2: Over-scaffolding `web/` in a backend migration milestone
**What goes wrong:**  
Placeholder frontend scope expands into framework/tooling debates and delays API stabilization.

**Prevention:**  
Keep `web/` minimal placeholder contract (README, run stub, env example) and defer product frontend decisions.

**Warning signs:**
- PRs introduce large frontend dependency trees unrelated to migration safety.
- API migration tasks blocked on frontend setup decisions.

**Phase mapping:**  
**Phase 1:** strict scope guardrails.

## Minor Pitfalls

### Pitfall 1: Tooling docs lag behind structure
**What goes wrong:**  
README/runbooks/onboarding still reference root commands and paths.

**Prevention:**  
Treat docs update as definition-of-done for each migration phase.

**Warning signs:**
- New contributors fail first-run setup.
- Frequent “docs are outdated” comments on PRs.

**Phase mapping:**  
**Phase 3 (Hardening):** documentation parity pass.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: Folder migration (`api/`, `web/`) | Import/path breakage and config leakage | Lock import root strategy; enforce app-local env files only; add boot smoke tests |
| Phase 1: Independent run commands | Command sprawl/no canonical entrypoints | Publish single command contract per app and enforce in CI/docs |
| Phase 2: CI migration | Wrong working-directory, stale paths, skipped tests | Split app jobs; set explicit working dirs; assert collected test count |
| Phase 2: Test/config relocation | Pytest rootdir drift | Standardize invocation path and one config source |
| Phase 3: Deployment/runtime hardening | Env precedence surprises across environments | Validate env precedence and run startup config sanity checks |

## Sources

- Pydantic Settings docs (env file usage + precedence): https://github.com/pydantic/pydantic-settings/blob/main/docs/index.md (**HIGH**)  
- Pytest docs (rootdir and config discovery behavior): https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/customize.md (**HIGH**)  
- Uvicorn settings docs (`--app-dir`, reload dir semantics): https://github.com/kludex/uvicorn/blob/main/docs/settings.md (**HIGH**)  
- GitHub Actions docs (default working-directory): https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/setting-a-default-shell-and-working-directory (**HIGH**)  
- Docker Compose docs (env files, interpolation, precedence):  
  - https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/  
  - https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/ (**HIGH**)  
- Python docs (`sys.path` initialization and execution context impact): https://docs.python.org/3/library/sys_path_init.html (**HIGH**)
