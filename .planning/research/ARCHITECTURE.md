# Architecture Patterns

**Domain:** React/Express + Python FastAPI Monorepo
**Researched:** 2026-04-12
**Overall confidence:** HIGH

## Recommended Architecture

The system should follow a **BFF (Backend-For-Frontend) Pattern** or **API Gateway Pattern** within a monorepo structure.

1.  **Frontend (React):** Single Page Application handling UI and user interactions.
2.  **Web Server / BFF (Express):** Serves the built React static assets and acts as a proxy/gateway to the Python backend. It handles frontend-specific concerns (like SSR if added later, frontend routing, or UI-specific data aggregation).
3.  **Backend API (FastAPI):** Core domain logic, heavy computation (LightGBM predictions), and direct external API integrations (Kraken).

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **React UI** (`/web/client`) | Renders the dashboard, captures user SL/TP controls | Express Server (via HTTP/REST) |
| **Express Server** (`/web/server`) | Serves React assets, proxies API requests, frontend config | React UI (incoming), FastAPI (outgoing) |
| **FastAPI Backend** (`/api`) | OHLCV data fetching, ML inference, core trading logic | Express Server (incoming), Kraken API (outgoing) |

## Data Flow

1.  **User Request:** User opens the dashboard in their browser.
2.  **Static Serving:** Browser requests assets from the Express Server. Express serves the React application.
3.  **Data Hydration:** React UI requests live OHLCV data and predictions (e.g., `GET /api/v1/historic-data/live`).
4.  **Proxying:** The Express Server receives this request at `/api/...` and transparently proxies it to the FastAPI Backend (e.g., `http://localhost:8000/api/...`).
5.  **Execution:** FastAPI queries Kraken, runs the LightGBM model, and returns the JSON payload.
6.  **Response:** The Express Server forwards the JSON payload back to the React UI for rendering.

## Suggested Build Order

To ensure a smooth integration without breaking existing functionality, the build order should be:

1.  **Phase 1: Foundation & Scaffold**
    *   Create the `/web` directory structure.
    *   Initialize the Express server with basic proxy middleware (`http-proxy-middleware` or similar) pointing to the FastAPI backend.
    *   Set up the unified startup script (e.g., using `concurrently` in the root `package.json` or a custom script) to run both servers.
2.  **Phase 2: UI Implementation (React)**
    *   Scaffold the React application (e.g., Vite) inside `/web`.
    *   Configure Express to serve the built React static files.
    *   Integrate the Stitch "Forex Dashboard with SL/TP Controls" template.
3.  **Phase 3: Integration & Wiring**
    *   Wire the React components to call the Express API routes.
    *   Ensure CORS and proxy configurations are correctly routing requests to the FastAPI backend.

## Patterns to Follow

### Pattern 1: API Proxying in Express
**What:** Using Express to proxy `/api` requests to FastAPI.
**When:** Always in local development and standard deployments to avoid CORS issues and simplify the frontend's API base URL.
**Example:**
```javascript
// Express setup
const { createProxyMiddleware } = require('http-proxy-middleware');
app.use('/api', createProxyMiddleware({ 
  target: process.env.FASTAPI_URL || 'http://localhost:8000', 
  changeOrigin: true 
}));
```

### Pattern 2: Unified Monorepo Runner
**What:** A single script that boots both the Python and Node environments.
**When:** For developer experience (DX) and CI/CD consistency.
**Example:** Using npm `concurrently` in a root `package.json`:
```json
"scripts": {
  "start": "concurrently \"npm run start:api\" \"npm run start:web\"",
  "start:api": "cd api && uvicorn app.main:app --reload",
  "start:web": "cd web && npm run dev"
}
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Direct UI-to-FastAPI Communication (in Production)
**What:** Having the React app make cross-origin requests directly to FastAPI, bypassing Express.
**Why bad:** Introduces complex CORS management, exposes the backend URL directly, and splits deployment concerns.
**Instead:** Always route UI API calls through the Express server via a proxy setup.

### Anti-Pattern 2: Duplicating Business Logic
**What:** Implementing data transformations or OHLCV formatting in the Express layer.
**Why bad:** The FastAPI backend is already the authoritative source for ML and data processing (using Pandas/NumPy). Replicating this in Node/Express creates maintenance overhead.
**Instead:** Express should remain a "dumb" proxy for API requests, only handling UI-specific formatting if absolutely necessary.

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| **API Load** | Single Uvicorn worker | Gunicorn with multiple Uvicorn workers | Horizontal pod scaling (K8s) for FastAPI |
| **Static Assets** | Express serves static files | CDN (Cloudflare/AWS CloudFront) serves React assets | CDN + Edge caching |

## Sources

- General BFF (Backend-For-Frontend) Architecture Patterns
- Monorepo structural best practices (React + Express proxying)
