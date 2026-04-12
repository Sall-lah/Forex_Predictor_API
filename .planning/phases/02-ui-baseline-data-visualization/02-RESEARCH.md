# Phase 02: UI Baseline & Data Visualization - Technical Research

## Execution Strategy
- Ensure `lightweight-charts` is installed in `web/` and integrated into the template.
- Implement polling in a custom React hook `useMarketData` querying `/api/v1/historic-data/live`.
- Integrate connection health status via `useHealthCheck` or inline error handling.

## Code Patterns
- Use React 19 and Vite.
- Connect to Express proxy at `/api/v1/...`.

## Potential Pitfalls
- Frequent polling causing React re-renders. Use `useRef` or lightweight-charts native update methods where possible.
- Chart container resizing issues.
