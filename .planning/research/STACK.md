# Stack Research

**Domain:** Python FastAPI API + frontend placeholder monorepo
**Researched:** 2026-04-11
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.135.3 | Backend HTTP API framework in `api/` | Current FastAPI standard for typed Python APIs; strong OpenAPI support and clean migration from existing codebase. |
| uv | 0.11.6 | Python package/project manager for `api/` | 2025+ standardizing quickly: lockfile-based reproducibility, fast installs, and native workspace support for monorepo-style Python management. |
| pnpm | 10.33.0 | JS package manager + workspace root orchestration | De-facto monorepo package manager pattern for JS/TS side; strict dependency boundaries and single workspace lockfile behavior. |
| Turborepo (`turbo`) | 2.9.6 | Cross-app task orchestration (`api` + `web`) | Standard monorepo task runner pattern for caching/parallel runs; gives independent app commands plus unified root workflows. |
| Vite | 8.0.8 | `web/` placeholder app runtime/build tool | Fastest low-friction placeholder scaffold for independent frontend execution; easy to keep minimal until real web implementation starts. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.12.5 | API schema validation/model typing | Always in FastAPI app contracts and settings models. |
| pydantic-settings | 2.13.1 | App-local env/config loading | Always for per-app env isolation (`api/.env`), with explicit config pathing after migration. |
| Uvicorn | 0.44.0 | ASGI runtime process | Always for dev/prod app serving (`uv run fastapi dev` locally, `fastapi run`/`uvicorn` in containers). |
| Ruff | 0.15.10 | Lint + formatting | Use as default Python quality gate; replaces multi-tool lint stacks for faster CI and simpler config. |
| Pytest | 9.0.3 | Backend test runner | Keep existing test strategy; run package-scoped from `api/`. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Node.js | 20.19+ LTS | Runtime for `web/`, pnpm, turbo | Required by modern Vite 8 line; pin in repo docs/CI to avoid local mismatch. |
| Corepack | Package manager pinning | Enable and pin pnpm version at repo root for deterministic onboarding. |
| Docker | Deployment/runtime packaging | Build FastAPI image from official Python base; do not use deprecated FastAPI base images. |

## Installation

```bash
# Root (JS workspace orchestration)
corepack enable
corepack prepare pnpm@10.33.0 --activate
pnpm add -D turbo@2.9.6

# Web placeholder app
pnpm create vite web --template react-ts

# API (inside api/)
uv init --app
uv add fastapi==0.135.3 pydantic==2.12.5 pydantic-settings==2.13.1 uvicorn==0.44.0 httpx==0.28.1
uv add --dev ruff==0.15.10 pytest==9.0.3
uv lock
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| pnpm workspaces | npm workspaces | Only if team policy forbids pnpm; otherwise pnpm is better for strictness/perf in monorepos. |
| Turborepo | Nx | Choose Nx if you need graph visualization/generators/policies at enterprise scale from day one. |
| Vite placeholder | Next.js app scaffold | Choose Next.js only if you already know the web app will need SSR/full-stack React immediately. |
| uv | Poetry | Choose Poetry if org-standard tooling is already Poetry and migration cost outweighs uv benefits. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Root-level shared `.env` for both apps | Causes config leakage and accidental cross-app coupling | App-local env files (`api/.env`, `web/.env`) with separate loaders. |
| Deprecated `tiangolo/uvicorn-gunicorn-fastapi` Docker base image | Official FastAPI docs mark it deprecated; unnecessary complexity now that `fastapi`/`uvicorn` support workers directly | Build from `python` base image and run `fastapi run`/`uvicorn` explicitly. |
| Conda + pip dual source of truth for app dependencies | Drift-prone, hard to reproduce in CI/containers | `pyproject.toml` + `uv.lock` as single Python dependency source. |

## Stack Patterns by Variant

**If this milestone remains “backend migration + web placeholder”:**
- Use React + Vite only as a thin independently runnable shell (`web/`).
- Because it minimizes frontend commitment while proving monorepo boundaries now.

**If frontend later needs SSR/server rendering:**
- Keep monorepo shape, swap `web/` to Next.js or React Router framework mode.
- Because `api/` stays independently deployable, and frontend can evolve without redoing API packaging.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Vite 8.0.8 | Node.js ^20.19.0 \|\| >=22.12.0 | Pin Node 20.19+ in local + CI immediately. |
| FastAPI 0.135.3 | Pydantic 2.x | Current FastAPI ecosystem standard is Pydantic v2-based. |
| uv 0.11.6 | `pyproject.toml` + `uv.lock` | Use `uv sync`/`uv run --frozen` in CI for reproducibility. |
| pnpm 10.33.0 | Workspace root `pnpm-workspace.yaml` | Supports single shared lockfile and explicit workspace protocol behavior. |

## Sources

- Context7 `/astral-sh/uv` — workspace support, lock/sync behavior, FastAPI integration guidance (HIGH)
- Context7 `/fastapi/fastapi` — Docker deployment guidance, workers, deprecated base image warning (HIGH)
- Context7 `/websites/pnpm_io` — workspace settings, shared lockfile, `workspace:` protocol (HIGH)
- PyPI JSON API: `fastapi`, `pydantic`, `pydantic-settings`, `uvicorn`, `uv`, `ruff`, `pytest`, `httpx` — current versions (MEDIUM)
- npm registry `latest`: `pnpm`, `turbo`, `vite`, `react`, `typescript` — current versions (MEDIUM)
- Official docs: https://vite.dev/guide/ (Node compatibility + monorepo suitability), https://react.dev/learn/start-a-new-react-project, https://pnpm.io/workspaces (MEDIUM)

---
*Stack research for: Forex Predictor API monorepo restructure*
*Researched: 2026-04-11*
