# Technology Stack

**Analysis Date:** 2026-04-12

## Languages

**Primary:**
- Python 3.12 - API runtime, ML inference, and data processing (`api/app/`)
- TypeScript / TSX - Web application frontend and server (`web/src/`, `web/server/`)

**Secondary:**
- HTML/CSS - Web application styling and markup (Tailwind CSS, `web/index.html`)
- JavaScript - Configuration and build output (`web/tailwind.config.js`, `web/postcss.config.js`)
- YAML/INI - Configuration (`api/environment.yml`, `api/pytest.ini`)

## Runtime

**Environment:**
- Node.js - Web application runtime and build tools (`web/`, root)
- CPython 3.12 - API runtime managed via conda environment named `forex_prediction` (`api/`)

**Package Manager:**
- npm - Web and monorepo dependencies (`package.json`, `web/package.json`)
- conda/pip - Python environment and dependencies (`api/environment.yml`, `api/requirements.txt`)
- Lockfile: `package-lock.json` present at root and in `web/`. No lockfile detected in `api/`.

## Frameworks

**Core:**
- FastAPI - HTTP API framework for the backend (`api/app/main.py`)
- React 19 - UI library for the frontend (`web/src/`)
- Express 5 - Production server for the web frontend (`web/server/`)

**Testing:**
- pytest - Test runner for the Python backend (`api/tests/`, `api/pytest.ini`)
- Testing framework for Web not detected.

**Build/Dev:**
- Vite 8 - Build tool and dev server for the React frontend (`web/vite.config.ts`)
- Uvicorn - ASGI server for running the FastAPI backend (`api/app/main.py`)
- concurrently - Monorepo script execution (`package.json`)
- Tailwind CSS 4 & PostCSS - Utility-first styling framework (`web/tailwind.config.js`)

## Key Dependencies

**Critical:**
- `pandas==2.2.2` & `numpy==2.0.2` - Data manipulation and numeric operations (`api/requirements.txt`)
- `scikit-learn==1.6.1` & `lightgbm==4.6.0` - Machine learning inference engine (`api/requirements.txt`)
- `joblib==1.5.3` - Serialized model loading (`api/app/features/prediction/service.py`)
- `lightweight-charts` - Trading charts UI component (`web/package.json`)

**Infrastructure:**
- `httpx` - Outbound HTTP client for Kraken API calls (`api/app/shared/ohlcv/kraken_api.py`)
- `pydantic` & `pydantic-settings` - Typed config and validation (`api/app/core/config.py`)
- `http-proxy-middleware` - API proxying in the Express server (`web/package.json`)

## Configuration

**Environment:**
- Configured centrally via Pydantic `Settings` in `api/app/core/config.py` using `.env`
- Base variables provided in `api/.env.example`

**Build:**
- Root: `package.json` for monorepo tasks (`npm run dev`)
- Backend: `api/environment.yml`, `api/requirements.txt`, `api/pytest.ini`
- Frontend: `web/package.json`, `web/vite.config.ts`, `web/tailwind.config.js`, `web/postcss.config.js`, `web/tsconfig.json`

## Platform Requirements

**Development:**
- Node.js environment
- Python 3.12 (via conda or equivalent)
- Local ML model artifact at `api/app/features/prediction/ml_models/lightgbm_model_forex.pkl`

**Production:**
- Backend: ASGI deployment target running `app.main:app` (FastAPI + Uvicorn)
- Frontend: Node.js environment running `web/server/index.js` (Express)
- Configured to run locally via `npm run start` leveraging `concurrently`
- Network access to Kraken Public OHLC API

---

*Stack analysis: 2026-04-12*
