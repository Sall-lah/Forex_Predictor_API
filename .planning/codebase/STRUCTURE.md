# Codebase Structure

**Analysis Date:** 2026-04-12

## Directory Layout

```
/
├── api/                    # Backend API Application
│   ├── app/                # Application source code
│   │   ├── api/            # Router aggregation
│   │   ├── core/           # Configuration and exceptions
│   │   ├── features/       # Feature modules (historic_data, prediction)
│   │   ├── middleware/     # Rate limiting and other middleware
│   │   └── shared/         # Shared infrastructure (ohlcv)
│   ├── tests/              # Pytest test suite
│   └── environment.yml     # Conda environment definition
└── web/                    # Frontend React + Express Proxy Application
    ├── server/             # Express server logic
    │   └── routes/         # API proxy routes
    ├── src/                # React frontend code
    │   ├── assets/         # Static images, styles
    │   ├── components/     # Reusable UI components
    │   ├── hooks/          # React custom hooks
    │   ├── pages/          # Full page views
    │   ├── services/       # Frontend API client services
    │   └── types/          # TypeScript definitions
    └── package.json        # Frontend and Proxy dependencies
```

## Directory Purposes

**`api/app/features/`:**
- Purpose: Contains the core business logic separated by domain concepts.
- Contains: `router.py`, `schemas.py`, `service.py`.
- Key files: `api/app/features/prediction/service.py`, `api/app/features/historic_data/service.py`

**`api/app/shared/ohlcv/`:**
- Purpose: Shared transport and parsing logic for financial data.
- Contains: Kraken HTTP client wrapper, pandas DataFrame transformers.
- Key files: `api/app/shared/ohlcv/kraken_api.py`, `api/app/shared/ohlcv/ohlc_dataframe.py`

**`web/server/`:**
- Purpose: Hosts the Node/Express backend for serving static assets and proxying API calls.
- Contains: JS server entry point and simple route definitions.
- Key files: `web/server/index.js`, `web/server/app.js`

**`web/src/`:**
- Purpose: The React SPA codebase built with Vite and Tailwind.
- Contains: TypeScript/TSX source code for the UI.
- Key files: `web/src/main.tsx`, `web/src/App.tsx`

## Key File Locations

**Entry Points:**
- `api/app/main.py`: ASGI application definition and middleware registration.
- `web/server/index.js`: Express server start script.
- `web/src/main.tsx`: React application root.

**Configuration:**
- `api/app/core/config.py`: Pydantic settings loading `.env`.
- `api/environment.yml`: Conda dependencies for backend.
- `web/vite.config.ts`: Vite frontend bundler configuration.
- `web/tailwind.config.js`: Tailwind CSS styling rules.

**Core Logic:**
- `api/app/features/prediction/service.py`: ML inference using LightGBM model and `ta` indicators.

**Testing:**
- `api/tests/conftest.py`: Shared pytest fixtures.
- `api/tests/features/`: Tests aligning to the backend feature directories.

## Naming Conventions

**Files:**
- Backend Modules: `snake_case.py` (e.g. `rate_limit/middleware.py`)
- Frontend Components: `PascalCase.tsx` (e.g. `TradingDashboard.tsx`)
- Frontend Utilities: `camelCase.ts` (e.g. `apiClient.ts`)

**Directories:**
- Global: `snake_case` in backend (`historic_data`), `camelCase` in frontend if multiple words.

## Where to Add New Code

**New Backend Feature:**
- Directory: `api/app/features/[feature_name]/`
- Router: `api/app/features/[feature_name]/router.py`
- Implementation: `api/app/features/[feature_name]/service.py`
- Tests: `api/tests/features/[feature_name]/`

**New Frontend Page/Component:**
- Page Component: `web/src/pages/[PageName].tsx`
- Shared Component: `web/src/components/[ComponentName]/[ComponentName].tsx`
- API Fetch Logic: `web/src/services/[apiService].ts`

**Shared Backend Utilities:**
- Implementation: `api/app/shared/[module_name]/`

## Special Directories

**`api/app/features/prediction/ml_models/`:**
- Purpose: Contains serialized machine learning artifacts (`.pkl` files).
- Generated: Yes (from training scripts).
- Committed: Yes (currently used for inference).

**`web/dist/`:**
- Purpose: Compiled output of the React Vite build.
- Generated: Yes
- Committed: No (typically ignored).

---

*Structure analysis: 2026-04-12*