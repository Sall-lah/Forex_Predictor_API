# Technology Stack

**Project:** Forex Predictor API Monorepo Restructure
**Researched:** Sun Apr 12 2026
**Overall confidence:** HIGH

## Recommended Stack

### Core Frameworks
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| React | 19.x | Frontend UI | The modern standard for React development. Delivers robust concurrent rendering and improved hooks out of the box. |
| Vite | 6.x | Frontend Build Tooling | Replaces Webpack/CRA. Provides extremely fast HMR (Hot Module Replacement) and optimized production builds. |
| Express | 5.x | Frontend Server / API Gateway (BFF) | The standard Node web framework. Version 5 brings native Promise support for cleaner async route handlers. Serves the React app and proxies/orchestrates calls to the Python API. |
| FastAPI | (Existing) | Backend ML Engine | Preserved as-is from the current application. Excellent performance for Python ML inference. |

### Monorepo & Concurrency
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| concurrently | 9.x | Unified Startup Script | The simplest and most reliable way to run multiple processes (Node Express + Python Uvicorn) from a single root `npm start` command. Streamlines developer experience without complex infrastructure. |
| npm workspaces | v10+ | Dependency Management | Built into modern NPM. Cleanly separates the `web/` dependencies from the root orchestration without needing extra tools like Lerna. |

### API Communication
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Native Fetch | Built-in | Client-to-BFF | The 2026 standard for making HTTP requests from React. No need for heavy external libraries like Axios. |
| http-proxy-middleware | 3.x | Express-to-FastAPI Proxy | Use in Express to seamlessly proxy frontend API requests (`/api/*`) to the FastAPI backend running on a different port. Avoids CORS issues and provides a single origin. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Monorepo Runner | `concurrently` | `Turborepo` / `Nx` | While powerful, they are overkill for a simple two-app (Node + Python) repository. They excel in multi-package Node ecosystems but add unnecessary configuration overhead for a simple start script. |
| Monorepo Runner | `concurrently` | `docker-compose` | Heavyweight for local rapid UI iteration. Better suited for production deployments, but `concurrently` offers a faster inner dev loop for the UI. |
| Frontend Server | Express 5 | Next.js | User explicitly requested React + Express. Next.js would combine these but changes the architectural requirement. Express acts perfectly as a lightweight Backend-For-Frontend (BFF). |

## Installation & Setup

### Root Orchestration (`/package.json`)
```json
{
  "name": "forex-predictor-monorepo",
  "private": true,
  "scripts": {
    "install:all": "npm install --prefix web && conda env update -f api/environment.yml",
    "dev:api": "cd api && uvicorn app.main:app --reload --port 8000",
    "dev:web": "npm run dev --prefix web",
    "dev": "concurrently -c \"cyan,magenta\" -n \"API,WEB\" \"npm run dev:api\" \"npm run dev:web\""
  },
  "devDependencies": {
    "concurrently": "^9.0.0"
  }
}
```

### Express Server (`/web/package.json`)
```bash
npm install express http-proxy-middleware
npm install -D typescript @types/express ts-node
```

### React App (`/web/client/package.json`)
```bash
npm create vite@latest client -- --template react-ts
```

## Anti-Patterns to Avoid

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Enabling CORS on FastAPI | Exposes the Python backend to direct browser access, bypassing the Express layer. | Use Express as a reverse proxy (`http-proxy-middleware`). The React app talks only to Express on the same origin, and Express talks to FastAPI on the internal network. |
| `create-react-app` | Deprecated and unmaintained. Slow build times. | Use Vite for scaffolding the React application. |
| Python Subprocess in Node | Using Node's `child_process.spawn` inside Express to run FastAPI creates tight coupling and zombie processes. | Keep processes separate and use a dedicated runner like `concurrently` at the repository root. |

## Sources
- Official Express 5.0 Release Documentation
- Vite 6 Documentation
- React 19 Upgrade Guide
- Concurrently GitHub Repository (Standard Monorepo Practices)
