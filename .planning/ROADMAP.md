# Roadmap

## Phases

- [ ] **Phase 1: Foundation & Orchestration** - Unified monorepo setup with Express proxy and React scaffold
- [ ] **Phase 2: UI Baseline & Data Visualization** - Stitch template integration and live market charting
- [ ] **Phase 3: Trading Controls & Prediction Integration** - ML prediction overlay and risk management inputs

## Phase Details

### Phase 1: Foundation & Orchestration
**Goal**: Both applications can be started together with a single command, with traffic routing properly between them.
**Depends on**: None
**Requirements**: MONO-01, MONO-02, MONO-03, MONO-04, UI-03
**Success Criteria** (what must be TRUE):
  1. Running a single command from the project root starts both the FastAPI backend and Express web server.
  2. Stopping the runner cleanly terminates both processes without leaving zombie instances.
  3. The React app is accessible in the browser and successfully routes API requests to the backend via the Express proxy.
**Plans**: 2 plans
- [x] 01-01-PLAN.md — Scaffold React app and Express BFF
- [x] 01-02-PLAN.md — Root Orchestration Setup

### Phase 2: UI Baseline & Data Visualization
**Goal**: Users can view a styled dashboard displaying live market data and backend connectivity.
**Depends on**: Phase 1
**Requirements**: UI-01, UI-02, DASH-01, DASH-02, DASH-05
**Success Criteria** (what must be TRUE):
  1. Dashboard renders with the "Forex Dashboard with SL/TP Controls" Stitch template and design system.
  2. User can view an OHLCV candlestick chart populated with live historic data fetched from the backend.
  3. The current market price is distinctly displayed alongside the chart.
  4. A visual indicator accurately shows whether the backend/Kraken connection is healthy or failing.
**Plans**: 2 plans
- [ ] 02-01-PLAN.md — Scaffold UI baseline and Stitch layout
- [ ] 02-02-PLAN.md — Data polling hook and OHLCV chart implementation
**UI hint**: yes

### Phase 3: Trading Controls & Prediction Integration
**Goal**: Users can see ML predictions and input risk management parameters on the dashboard.
**Depends on**: Phase 2
**Requirements**: DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. The dashboard explicitly shows the LightGBM model's latest price movement prediction.
  2. User can type numerical values into Stop Loss (SL) and Take Profit (TP) input fields.
  3. The interface updates to reflect the latest prediction state after fetching from the backend.
**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Orchestration | 0/0 | Not started | - |
| 2. UI Baseline & Data Visualization | 0/0 | Not started | - |
| 3. Trading Controls & Prediction Integration | 0/0 | Not started | - |
