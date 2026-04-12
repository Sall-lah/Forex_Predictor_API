# Technology Stack

**Analysis Date:** 2026-04-12

## Languages

**Primary:**
- Python 3.12 - API runtime, ML inference, and data processing in `api/app/` (configured in `api/environment.yml`)

**Secondary:**
- YAML - conda environment specification in `api/environment.yml`
- INI - test runner configuration in `api/pytest.ini`
- Markdown - model usage documentation in `api/app/features/prediction/ml_models/MODEL_USAGE.md` and `api/app/features/prediction/ml_models/OHLCV_PREPROCESS.md`

## Runtime

**Environment:**
- CPython 3.12 (conda environment named `forex_prediction`)

**Package Manager:**
- conda - environment provisioning from `api/environment.yml`
- pip - Python packages listed in `api/requirements.txt`
- Lockfile: missing (no `poetry.lock`, `Pipfile.lock`, or similar at `api/` root)

## Frameworks

**Core:**
- FastAPI (version unpinned) - HTTP API framework in `api/app/main.py`, route composition in `api/app/api/router.py`, and feature routers in `api/app/features/*/router.py`
- Pydantic + pydantic-settings (versions unpinned) - request/response validation and settings management in `api/app/features/*/schemas.py` and `api/app/core/config.py`

**Testing:**
- pytest (version unpinned) - test runner configured in `api/pytest.ini` with tests under `api/tests/`
- pytest-cov (version unpinned) - coverage plugin from `api/requirements.txt`
- pytest-mock (version unpinned) - mocking utilities used in `api/tests/features/*`

**Build/Dev:**
- Uvicorn (version unpinned) - ASGI server for local/dev runtime (`uvicorn app.main:app` in `api/app/main.py`)

## Key Dependencies

**Critical:**
- `fastapi` (unpinned) - API app lifecycle, routing, and OpenAPI surface in `api/app/main.py` and `api/app/features/*/router.py`
- `httpx` (unpinned) - outbound Kraken OHLC HTTP calls in `api/app/shared/ohlcv/kraken_api.py`
- `pandas==2.2.2` - OHLCV parsing, timestamp handling, and feature DataFrame transforms in `api/app/shared/ohlcv/ohlc_dataframe.py` and `api/app/features/prediction/service.py`
- `numpy==2.0.2` - numeric coercion and finite-value validation for model inference in `api/app/features/prediction/service.py`
- `ta==0.11.0` - technical indicator generation in `api/app/features/prediction/service.py`
- `joblib==1.5.3` - serialized model artifact loading in `api/app/features/prediction/service.py`
- `scikit-learn==1.6.1` and `lightgbm==4.6.0` - model compatibility/runtime for `api/app/features/prediction/ml_models/lightgbm_model_forex.pkl` and prediction flow in `api/app/features/prediction/service.py`
- `python-dotenv` (unpinned) - `.env` loading support used through `pydantic-settings` env file config in `api/app/core/config.py`

**Infrastructure:**
- `pydantic-settings` (unpinned) - typed environment variable management in `api/app/core/config.py`
- `starlette` (FastAPI dependency) - middleware base/request/response classes in `api/app/middleware/rate_limit/middleware.py` and `api/app/middleware/rate_limit/service.py`

## Configuration

**Environment:**
- Central typed settings live in `Settings` in `api/app/core/config.py`, loaded via `get_settings()` and cached with `functools.lru_cache`
- Environment file loading is configured as `.env` via `model_config` in `api/app/core/config.py`
- Example environment file: `api/.env.example`

**Build:**
- Runtime/dependency manifests: `api/requirements.txt`, `api/environment.yml`
- Test config: `api/pytest.ini`
- Build/lint config files (`pyproject.toml`, `setup.cfg`, `.flake8`, `.prettierrc`) are not detected at `api/` root

## Platform Requirements

**Development:**
- Python 3.12 environment with conda/pip dependencies from `api/environment.yml` and `api/requirements.txt`
- Local readable model artifact at `api/app/features/prediction/ml_models/lightgbm_model_forex.pkl` (validated by `ModelLoader` in `api/app/features/prediction/service.py`)

**Production:**
- Outbound HTTPS access to Kraken public OHLC endpoint configured by `KRAKEN_OHLC_URL` in `api/app/core/config.py` (default: `https://api.kraken.com/0/public/OHLC`)
- ASGI deployment target running `app.main:app` (FastAPI + Uvicorn stack from `api/app/main.py` and `api/requirements.txt`)
- Environment-variable driven configuration compatible with `.env`/process environment values loaded by `api/app/core/config.py`

---

*Stack analysis: 2026-04-12*