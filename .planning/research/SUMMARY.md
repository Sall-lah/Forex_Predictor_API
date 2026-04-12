# Project Research Summary

**Project:** Forex Predictor API Monorepo Restructure
**Domain:** React/Express + Python FastAPI Monorepo (Forex Trading Dashboard)
**Researched:** 2026-04-12
**Confidence:** HIGH

## Executive Summary

The Forex Predictor API Monorepo Restructure is a technical effort to build a React-based trading dashboard alongside an existing Python FastAPI backend. The established industry standard for this type of application is the Backend-For-Frontend (BFF) pattern, where an Express.js server hosts the React static assets and acts as a reverse proxy to the Python machine learning API. This avoids complex cross-origin (CORS) security issues and allows clean separation of concerns.

The recommended approach leverages React 19 powered by Vite, Express 5 as the BFF, and the existing FastAPI application. Orchestration will be handled via a unified `concurrently` start script using npm workspaces to streamline the local developer experience without the overhead of heavy monorepo tools like Turborepo. Core features to focus on include live OHLCV candlestick charts, prediction overlays, and Stop Loss/Take Profit (SL/TP) controls, purposefully avoiding direct trade execution to minimize scope and liability.

The most critical risks to mitigate during implementation are process management failures (zombie Uvicorn processes when stopping the Node runner) and cross-origin resource sharing (CORS) nightmares caused by the React app directly calling the Python backend. Proper reverse proxying and robust exit signal handling in the root startup script are essential early-phase requirements.

## Key Findings

### Recommended Stack

The chosen stack prioritizes a lightweight, high-performance developer experience while preserving the existing backend as-is. We opted for a simple unified runner instead of complex monorepo infrastructure, recognizing the explicit 2-app boundary constraint.

**Core technologies:**
- **React 19 & Vite 6:** Frontend UI & Build Tooling — The modern standard for high-performance React applications.
- **Express 5:** Web Server & BFF — Acts as the single origin for the React app and proxies `/api` calls to FastAPI, avoiding CORS issues entirely.
- **FastAPI (Existing):** Backend ML Engine — Preserved as the existing core inference and data-fetching engine.
- **concurrently 9 & npm workspaces:** Monorepo Orchestration — Provides a unified `npm run dev` startup experience for both Node and Python environments.
- **http-proxy-middleware:** API Proxying — Enables seamless routing from Express to the FastAPI process.

### Expected Features

The feature set is highly constrained to analysis and prediction, intentionally excluding wallet management or trade execution.

**Must have (table stakes):**
- **Live Price Chart (OHLCV)** — Visualizing historical and live price action is essential.
- **Current Market Price Display** — Instant visibility into the current pricing.
- **Prediction Overlay / Status** — The core value prop; displaying the LightGBM model's next prediction.
- **Stop Loss (SL) & Take Profit (TP) Inputs** — Standard text/number inputs for risk management calculations.
- **API Connectivity Status** — Indicator showing if the backend/Kraken connection is healthy.

**Should have (competitive):**
- **Visual SL/TP Dragging on Chart** — Draggable lines for setting risk parameters directly on the chart.
- **Prediction Confidence Gauge** — Visualizing the model's certainty.
- **Backtest Simulation Overlay** — Showing historic prediction performance.

**Defer (v2+):**
- Dynamic SL/TP recommendations based on volatility.
- Multi-exchange support or social trading features.

### Architecture Approach

The architecture is built around a Backend-For-Frontend (BFF) pattern within a monorepo to maintain strong runtime isolation while enabling a unified development experience.

**Major components:**
1. **React UI (`/web/client`)** — Renders the trading dashboard and captures user inputs.
2. **Express Server (`/web/server`)** — Serves React static assets, manages frontend configuration, and proxies `/api/*` traffic.
3. **FastAPI Backend (`/api`)** — Handles OHLCV data fetching, ML inference, and external integrations (Kraken).

### Critical Pitfalls

1. **Zombie Backend Processes** — Avoided by using robust process managers (`honcho`/`foreman`) or explicitly handling SIGINT/SIGTERM in the Node runner to kill the Python child process.
2. **Cross-Origin Cookie & CORS Nightmares** — Avoided by strictly routing all UI API requests through the Express proxy rather than directly to FastAPI.
3. **Timezone & Timestamp Mismatches** — Avoided by standardizing all timestamps as Unix milliseconds before sending them to the React charting library.
4. **Over-fetching Live Data** — Avoided by aligning the React polling interval with the underlying OHLCV candle timeframe (e.g., polling every 1 minute for 1m candles).

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Monorepo Foundation & Orchestration
**Rationale:** The unified startup script and environment isolation are the biggest architectural risks. Building this first ensures developers don't suffer from zombie processes or env bleed.
**Delivers:** The root monorepo setup (`package.json`), `concurrently` runner script, and strict `.env` boundary rules.
**Addresses:** API Connectivity Status, Python environment setup.
**Avoids:** Zombie Backend Processes, Python Environment Activation Failures, Environment Variable Bleeding.

### Phase 2: Express BFF & Reverse Proxy
**Rationale:** Creating the API Gateway before the frontend prevents CORS issues from ever occurring.
**Delivers:** The `/web/server` Express application configured with `http-proxy-middleware` pointing to the FastAPI backend.
**Uses:** Express 5, `http-proxy-middleware`.
**Implements:** The Backend-For-Frontend proxy layer.
**Avoids:** Cross-Origin Cookie & CORS Nightmares.

### Phase 3: Frontend Scaffold & Charting
**Rationale:** The chart is the centerpiece of the dashboard and a prerequisite for all other visual features.
**Delivers:** Vite React app setup (`/web/client`), basic dashboard layout, and the Live Price Chart (OHLCV).
**Uses:** React 19, Vite 6.
**Addresses:** Live Price Chart (OHLCV), Current Market Price Display.
**Avoids:** Timezone & Timestamp Mismatches, Over-fetching Live Data.

### Phase 4: Prediction & Risk Controls Integration
**Rationale:** Adds the ML core value proposition on top of the established charting baseline.
**Delivers:** ML prediction overlay on the chart, basic SL/TP text inputs, and connectivity indicators.
**Addresses:** Prediction Overlay / Status, Stop Loss & Take Profit Inputs.
**Avoids:** Duplicating Business Logic (by relying entirely on the FastAPI backend for calculations).

### Phase Ordering Rationale

- **Infrastructure First:** By solving process management (Phase 1) and CORS/Proxying (Phase 2) first, we eliminate the most frustrating friction points for local UI development.
- **UI Dependency Chain:** The React chart (Phase 3) must be built before predictions or SL/TP controls (Phase 4) can be visualized on it.
- **Risk Mitigation:** Isolating the environments early guarantees the existing, stable FastAPI application is protected from accidental regressions.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** Needs research on the specific React charting library to use (e.g., Lightweight Charts vs. Recharts) to handle OHLCV financial data effectively.
- **Phase 4:** SL/TP state synchronization between chart overlays and text inputs often introduces complex state management needs.

Phases with standard patterns (skip research-phase):
- **Phase 1 & 2:** Express proxying and `concurrently` runners are well-documented, standard patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Express BFF + React Vite + Python is an industry standard approach. |
| Features | HIGH | Table stakes for trading dashboards are very well-established. |
| Architecture | HIGH | Monorepo proxy boundaries completely solve standard integration headaches. |
| Pitfalls | HIGH | Common monorepo and financial UI edge cases are well understood. |

**Overall confidence:** HIGH

### Gaps to Address

- **Charting Library Selection:** The specific React charting library wasn't definitively selected, though TradingView's Lightweight Charts is heavily implied as a standard. This needs validation during Phase 3 planning.
- **SL/TP State Management:** Need a defined strategy (e.g., Zustand vs React Context) for keeping visual drag-and-drop SL/TP controls synced with text inputs.

## Sources

### Primary (HIGH confidence)
- Official Express 5.0 Release Documentation — Express setup and proxying
- Vite 6 Documentation — Modern React build tooling
- General BFF (Backend-For-Frontend) Architecture Patterns — Proxy boundary validation

### Secondary (MEDIUM confidence)
- Monorepo structural best practices — `concurrently` and process management
- Established trading UX patterns (TradingView, MetaTrader)

---
*Research completed: 2026-04-12*
*Ready for roadmap: yes*