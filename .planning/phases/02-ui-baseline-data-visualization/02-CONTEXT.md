# Phase 2: UI Baseline & Data Visualization - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the foundational UI dashboard using the "Forex Dashboard with SL/TP Controls" Stitch template. Render a live OHLCV price chart, display the current market price, and show backend/Kraken API connectivity status.

</domain>

<decisions>
## Implementation Decisions

### Charting Library
- **D-01:** Lightweight Charts (TradingView) will be used for the OHLCV candlestick chart. High performance and native financial data support.

### API Polling Strategy
- **D-02:** Frequent Polling (1-5 seconds) for live OHLCV data to keep the chart live without overwhelming the REST API.

### Error Handling
- **D-03:** Status indicator + Warning overlay. The header indicator turns red and a non-intrusive 'stale data' warning overlay appears if the connection fails, keeping the chart visible.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specs
- `.planning/PROJECT.md` - Core project vision and constraints.
- `.planning/REQUIREMENTS.md` - Functional requirements for the dashboard.

### API Docs
- `api/app/features/prediction/ml_models/MODEL_USAGE.md` - ML model usage docs.
- `api/app/features/prediction/ml_models/OHLCV_PREPROCESS.md` - Preprocessing details for OHLCV.

</canonical_refs>

<code_context>
## Existing Code Insights

### Established Patterns
- **Backend API:** FastAPI REST API returning OHLCV data at `/api/v1/historic-data/live`.
- **Frontend Stack:** React 19 + Vite 6 + Express 5 BFF (from Phase 1 context).

### Integration Points
- Frontend will call Express BFF, which proxies to the FastAPI backend.
</code_context>

<specifics>
## Specific Ideas

No specific requirements - open to standard approaches based on the Stitch template.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 02-ui-baseline-data-visualization*
*Context gathered: 2026-04-12*