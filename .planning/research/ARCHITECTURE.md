# Architecture Research

**Domain:** API + web monorepo migration (FastAPI backend + placeholder web app)
**Researched:** 2026-04-11
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                           Monorepo Root                                 │
├──────────────────────────────────────────────────────────────────────────┤
│  apps/                                                                   │
│  ├── api/   (FastAPI service, owns backend runtime + tests + env)       │
│  └── web/   (frontend placeholder app, owns web runtime + env)           │
├──────────────────────────────────────────────────────────────────────────┤
│  tooling/                                                                 │
│  ├── scripts/   (repo-wide helper scripts; no app business logic)        │
│  ├── turbo.json (optional task graph for package-scoped runs)            │
│  └── docs/      (migration and runbook docs)                              │
└──────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `apps/api` | Own all backend code, Python deps, tests, model artifact paths, API run/start | Keep current FastAPI layered structure (`app/`, `tests/`, settings) moved under `apps/api/` |
| `apps/web` | Own all frontend code and web run/start (placeholder now) | Minimal scaffold with independent package/runtime and starter route |
| Repo root | Orchestrate cross-app commands and shared docs only | Task runner config (`turbo` optional), CI entrypoints, migration notes |
| Shared config contract (not shared secrets) | Define interface between apps (URLs, API contract, CORS assumptions) | Checked-in examples (`.env.example` per app), OpenAPI/typed client later |

## Recommended Project Structure

```text
Forex_Predictor_API/
├── apps/
│   ├── api/
│   │   ├── app/                       # existing FastAPI code moved from root
│   │   ├── tests/                     # existing tests moved with API
│   │   ├── requirements.txt           # Python deps owned by API
│   │   ├── environment.yml            # Conda env owned by API
│   │   ├── pytest.ini                 # API test config
│   │   ├── .env                       # API-only secrets/config (gitignored)
│   │   └── .env.example               # API env contract
│   ├── web/
│   │   ├── src/                       # placeholder web source
│   │   ├── package.json               # web deps/scripts
│   │   ├── .env.local                 # web-only config (gitignored)
│   │   └── .env.example               # web env contract
│   └── README.md                      # app-specific run commands
├── docs/
│   └── migration/
│       └── monorepo-move.md           # move plan + rollback checklist
├── turbo.json                         # optional, for filtered runs per app
└── .gitignore
```

### Structure Rationale

- **`apps/api` boundary:** safest migration path is “move-as-is first, refactor second”. Keep backend internals unchanged while only updating import/run paths.
- **`apps/web` boundary:** isolates future frontend decisions and avoids polluting backend dependency/runtime assumptions.
- **Per-app env files:** prevents cross-app leakage and keeps local/dev/prod configuration explicit by ownership.
- **Root as orchestrator only:** avoids accidental coupling; root should schedule tasks, not host app logic.

## Architectural Patterns

### Pattern 1: App-Owned Runtime Boundary

**What:** Each app owns its runtime, dependency manifest, and startup commands.
**When to use:** Always for API + web monorepo where services must run independently.
**Trade-offs:** Slight duplication (`.env.example`, scripts) but significantly lower coupling and safer releases.

**Example:**
```bash
# API only
python -m uvicorn app.main:app --reload --app-dir apps/api

# Web only (placeholder)
npm run dev --prefix apps/web
```

### Pattern 2: Config Ownership + Explicit Consumption

**What:** Config is private to app boundary; cross-app values flow through explicit variables (e.g., `WEB_API_BASE_URL` in web, `ALLOWED_ORIGINS` in api).
**When to use:** Any multi-app repo with independent deployability.
**Trade-offs:** Requires discipline in naming/versioning config contract, but eliminates “hidden global env” failures.

**Example (API settings):**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env",), env_file_encoding="utf-8")
    api_prefix: str = "/api/v1"
    allowed_origins: list[str] = ["http://localhost:3000"]
```

### Pattern 3: Filtered Task Execution (optional Turborepo)

**What:** Use package filters so api/web run/test/build independently.
**When to use:** Once web introduces Node tooling; useful for CI and local speed.
**Trade-offs:** Adds toolchain complexity, but improves ergonomics and cacheability.

**Example:**
```bash
turbo run dev --filter=api
turbo run dev --filter=web
```

## Data Flow

### Runtime/Data Flow Direction

```text
[web app]
   │  (HTTP calls using WEB_API_BASE_URL)
   ▼
[api routers/services]
   │
   ├──> [Kraken API]
   └──> [Local model artifact in apps/api/.../ml_models]
```

### Config Flow Direction (critical)

```text
apps/api/.env      ──> api Settings (pydantic-settings) ──> API runtime only
apps/web/.env.local ─> web runtime config                ──> Web runtime only

No direct .env sharing between apps.
Cross-app coordination only through explicit public values
(e.g., web knows API base URL; api knows allowed web origins).
```

### Key Data/Config Flows

1. **Web → API:** web reads its own base URL config and sends HTTP to API endpoints.
2. **API internal:** API reads only `apps/api/.env`, fetches OHLCV, runs prediction model, returns JSON.
3. **CORS/control plane:** API allowlist references web origin via API-owned env key (not by reading web env file).

## Migration-Safe Build Order (for Roadmap Sequencing)

1. **Phase A — Establish boundaries without behavior changes**
   - Create `apps/api` and `apps/web` skeleton.
   - Move backend files into `apps/api` with minimal path edits.
   - Keep endpoints and response contracts unchanged.

2. **Phase B — Restore independent run/test parity**
   - Update API run/test commands to execute from `apps/api`.
   - Add placeholder `apps/web` run command.
   - Verify API tests pass from new location before any refactor.

3. **Phase C — Isolate env/config ownership**
   - Introduce `apps/api/.env` and `apps/web/.env.local` patterns.
   - Add per-app `.env.example` and fail-fast validation in startup.
   - Remove/avoid root-level runtime `.env` dependence.

4. **Phase D — Add repo orchestration (optional turbo/CI matrix)**
   - Add filtered tasks (`--filter`) for app-specific runs.
   - In CI, run API checks independently from web placeholder checks.

5. **Phase E — Contract hardening**
   - Lock explicit API base URL + CORS contract.
   - Add migration guardrails (smoke tests, rollback notes).

**Why this order:** it minimizes risk by preserving backend behavior first, then restoring operational parity, then tightening config isolation. Refactor/tooling comes after correctness is re-established.

## Anti-Patterns

### Anti-Pattern 1: Root-Level Shared `.env` for Both Apps

**What people do:** Keep one repo `.env` consumed by API and web.
**Why it’s wrong:** Causes config leakage, accidental overrides, and deploy coupling.
**Do this instead:** Use app-local env files and explicit cross-app contract keys.

### Anti-Pattern 2: Refactor While Relocating

**What people do:** Move folders and redesign architecture simultaneously.
**Why it’s wrong:** Makes regressions hard to isolate and rollback risky.
**Do this instead:** Move first with parity tests, then refactor in later phases.

### Anti-Pattern 3: Shared Runtime Dependencies at Root

**What people do:** Put Python and Node runtime deps in one global place.
**Why it’s wrong:** Breaks independent runs and increases environment drift.
**Do this instead:** Keep dependencies app-owned; root only orchestrates.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Kraken OHLC API | API-only outbound HTTP via `apps/api` service layer | Keep transport + parsing inside API boundary |
| Model artifact | API local filesystem dependency | Use API-relative path config post-migration |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `apps/web` ↔ `apps/api` | HTTP API contract only | No direct imports across app boundaries |
| Repo root ↔ apps | Task orchestration only | Root should not own app secrets/runtime config |

## Sources

- FastAPI docs: Bigger Applications / `APIRouter` and `include_router` patterns (Context7: `/fastapi/fastapi`) — HIGH
- Pydantic Settings docs: `env_file`, multiple dotenv files, source precedence customization (Context7: `/pydantic/pydantic-settings`) — HIGH
- Turborepo docs: `--filter`, `envMode`, `globalDependencies` for env-aware task orchestration (Context7: `/vercel/turborepo`) — MEDIUM (optional tooling for this Python-first repo)

---
*Architecture research for: API + web monorepo migration*
*Researched: 2026-04-11*
