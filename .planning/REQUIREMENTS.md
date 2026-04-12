# Requirements: Forex Predictor Monorepo & Frontend

**Defined:** 2026-04-12
**Core Value:** A unified, easily runnable Forex trading dashboard that combines the existing backend prediction engine with a new React-based user interface.

## v1 Requirements

### Monorepo Setup

- [x] **MONO-01**: Create a frontend application in the `/web/` directory
- [x] **MONO-02**: Use React for the frontend UI
- [x] **MONO-03**: Use Express for the frontend server/API gateway (Backend-for-Frontend proxy)
- [x] **MONO-04**: Create a unified startup script (e.g. using concurrently) to run both the FastAPI bot API and the Express web server concurrently with a single command

### UI Design & Integration

- [x] **UI-01**: Use the Stitch project "Forex Predictor Dashboard" for the design system
- [x] **UI-02**: Use "Forex Dashboard with SL/TP Controls" as the specific frontend template/screen
- [x] **UI-03**: Integrate Context7 MCPs for documentation during development where necessary

### Dashboard Features

- [ ] **DASH-01**: Display Live Price Chart (OHLCV) using data from `/api/v1/historic-data/live`
- [ ] **DASH-02**: Display Current Market Price clearly
- [ ] **DASH-03**: Display Prediction Overlay / Status showing the LightGBM model's next prediction from `/api/v1/prediction/predict`
- [ ] **DASH-04**: Provide manual input controls for Stop Loss (SL) and Take Profit (TP)
- [ ] **DASH-05**: Display API Connectivity Status to show health of the backend/Kraken connection

## v2 Requirements

Deferred to future release.

### Advanced Features

- **FEAT-01**: Visual SL/TP Dragging on Chart
- **FEAT-02**: Prediction Confidence Gauge (if backend exposes probability)
- **FEAT-03**: Backtest Simulation Overlay
- **FEAT-04**: Dynamic SL/TP Recommendations based on volatility

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Direct Order Execution / Wallet Management | Out of scope, massive regulatory/security risk. Purely informational dashboard. |
| Multi-Exchange Aggregation | Backend is Kraken-focused. Adding others breaks scope. |
| Social Trading / Chat | Distraction from core AI prediction value proposition. |
| Changes to existing ML model | Focus is entirely on frontend integration and monorepo setup. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MONO-01 | Phase 1 | Complete |
| MONO-02 | Phase 1 | Complete |
| MONO-03 | Phase 1 | Complete |
| MONO-04 | Phase 1 | Complete |
| UI-01 | Phase 2 | Complete |
| UI-02 | Phase 2 | Complete |
| UI-03 | Phase 1 | Complete |
| DASH-01 | Phase 2 | Pending |
| DASH-02 | Phase 2 | Pending |
| DASH-03 | Phase 3 | Pending |
| DASH-04 | Phase 3 | Pending |
| DASH-05 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-12*
*Last updated: 2026-04-12 after initialization*