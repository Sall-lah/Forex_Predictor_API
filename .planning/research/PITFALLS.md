# Domain Pitfalls

**Domain:** React + Express + Python FastAPI Monorepo Integration & Forex Dashboard
**Researched:** 2026-04-12

## Critical Pitfalls

Mistakes that cause rewrites, broken deployments, or major operational issues.

### Pitfall 1: Zombie Backend Processes
**What goes wrong:** Developers use a Node runner (like `concurrently`) or a simple bash script to run both Express and FastAPI. When they hit `Ctrl+C`, the Node process terminates, but the Python Uvicorn server is orphaned and keeps running in the background.
**Why it happens:** OS signals (SIGTERM/SIGINT) are not propagated correctly across runtime boundaries (Node -> Shell -> Python Virtualenv/Conda).
**Consequences:** Port 8000 stays in use. The next time the developer runs the startup script, it crashes with `OSError: [Errno 98] Address already in use`. Developers are forced to manually find and kill PIDs.
**Prevention:** Use a robust process manager designed for cross-platform signal handling (e.g., `foreman`, `PM2`, or `honcho`), or ensure the custom Node startup script explicitly tracks/kills child process PIDs on exit.
**Detection:** The laptop fan spins up while "idle", or `EADDRINUSE` errors appear immediately on restart.
**Phase to Address:** Phase 2 (Infrastructure & Startup Scripting)

### Pitfall 2: Cross-Origin Cookie & CORS Nightmares
**What goes wrong:** The React frontend (running on port 3000) tries to call the FastAPI backend (on port 8000) directly. Preflight `OPTIONS` requests fail, or authentication cookies/headers are dropped by the browser.
**Why it happens:** The Express server is treated only as a static file host, rather than an API Gateway/BFF (Backend-For-Frontend).
**Consequences:** Hours lost configuring FastAPI CORS middleware, and fragile client-side code that breaks in production when ports/domains change.
**Prevention:** Explicitly configure the Express server to proxy `/api` requests to the Python backend (e.g., using `http-proxy-middleware`). The React app should only ever make requests to its own origin (the Express server).
**Detection:** `Access-Control-Allow-Origin` errors flooding the browser console during local development.
**Phase to Address:** Phase 3 (Express Server Setup)

### Pitfall 3: Timezone & Timestamp Mismatches
**What goes wrong:** Candlesticks render out of order or with gaps, and predictions overlay on the wrong candles.
**Why it happens:** The Python API (`pandas`) outputs UTC timestamps, but the React charting library expects Unix timestamps in milliseconds or local timezone data.
**Consequences:** The entire dashboard becomes useless for technical analysis.
**Prevention:** Standardize all timestamp passing as Unix milliseconds. Convert explicitly in the Express BFF or React data parsing layer.
**Detection:** Visual gaps in the chart, or the "Current Price" cursor trailing behind the last candle.
**Phase to Address:** Phase 4 (Frontend Features)

### Pitfall 4: Over-fetching Live Data
**What goes wrong:** The React frontend polls the `/historic-data/live` endpoint too aggressively, hitting rate limits or overwhelming the Kraken API proxy.
**Why it happens:** React Query or `useEffect` loops are configured to poll every second, but the underlying Kraken data (e.g., 1h or 15m candles) doesn't update that fast.
**Consequences:** API rate limits get triggered (existing `RateLimitMiddleware`), breaking the UI.
**Prevention:** Align frontend polling intervals with the actual timeframe of the OHLCV data being requested (e.g., poll every 30s for 1m candles, every 5m for 1h candles).
**Detection:** Frequent 429 Too Many Requests errors in the network tab.
**Phase to Address:** Phase 4 (Frontend Features)

## Moderate Pitfalls

### Pitfall 5: Environment Variable Bleeding
**What goes wrong:** A single `.env` file at the root of the monorepo is loaded by both the Node build process and the Python backend.
**Prevention:** Maintain strict separation of concerns. Use `api/.env` for backend secrets and `web/.env` for frontend configuration. Do not merge them globally. The React build must only embed variables explicitly prefixed with `REACT_APP_` or `VITE_`.
**Detection:** Backend secrets (like API keys or DB passwords) appear in the minified `main.[hash].js` bundle in the browser's DevTools network tab.
**Phase to Address:** Phase 2 & 3 (Configuration Architecture)

### Pitfall 6: Python Environment Activation Failures
**What goes wrong:** The unified root startup script (`npm start`) fails to activate the `conda` environment before running `uvicorn`. It falls back to the system Python, resulting in `ModuleNotFoundError: No module named fastapi`.
**Prevention:** The startup script must explicitly execute using the environment's python executable rather than relying on the ambient shell state. For example, use `conda run -n forex_prediction uvicorn ...` instead of just `uvicorn`.
**Detection:** The API runs fine when started manually inside the `api/` folder, but crashes immediately when started via the monorepo root script.
**Phase to Address:** Phase 2 (Infrastructure & Startup Scripting)

### Pitfall 7: State Desync on SL/TP Visual Dragging
**What goes wrong:** A user drags a Stop Loss line on the chart, but the text input field doesn't update, or vice versa.
**Prevention:** Maintain a single source of truth for SL/TP state in React (e.g., a shared context or Zustand store), ensuring both the Chart overlay and the Input forms subscribe to and mutate this single state.
**Phase to Address:** Phase 5 (SL/TP Integration)

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **Phase 2: Unified Runner** | Zombie PIDs holding ports open on restart | Use `honcho`/`foreman` or strict Node child_process teardown capturing SIGINT. |
| **Phase 3: Web Server Setup** | Complex CORS issues between React and FastAPI | Use Express as a reverse proxy for all `/api/*` traffic to FastAPI. |
| **Phase 4: Frontend Charting** | Canvas rendering blocks the main thread | Use a WebGL or highly optimized Canvas library; limit initial fetch to 500 candles. |
| **Phase 5: SL/TP Controls** | Floating point math errors | Use a library like `decimal.js` or parse everything as integers (pips). |

## Sources

- Domain Expertise: Multi-language (Node/Python) monorepo architecture patterns.
- Best Practices for Backend-For-Frontend (BFF) architecture.
- Node.js `child_process` signal propagation documentation.
- Common frontend UI/UX engineering lessons from Trading Platforms.