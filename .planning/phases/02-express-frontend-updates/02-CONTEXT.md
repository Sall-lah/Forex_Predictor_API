# Phase 2: Express / Frontend Updates - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Updating the Express proxy and React frontend to support UI selection of the timeframe interval. This connects the backend interval feature (built in Phase 1) to the user interface, utilizing the specified Stitch project for the UI baseline.

</domain>

<decisions>
## Implementation Decisions

### Transition State
- **D-01:** Keep old data visible on the chart and overlay a translucent loading spinner when switching intervals. This provides a smoother user experience compared to clearing the chart entirely.

### Default Interval
- **D-02:** Use 60 minutes (1H) as the default interval. This preserves backward compatibility and matches the current backend default.

### Interval Selector
- **D-03:** Display the interval selector as a Toggle Button Group right above the chart (e.g., [15m] [1H] [4H] [1D]). This is a common and intuitive trading UI pattern.

### Proxy Validation
- **D-04:** The Express proxy should act as a simple passthrough for the interval parameter. The FastAPI backend already handles robust validation (completed in Phase 1), making redundant validation or logging in Express unnecessary.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specs
- `.planning/PROJECT.md` — Defines monorepo constraints and requires the use of the specified Stitch project ("Forex Predictor Dashboard" - `885434743592032491`) and screen (`eadc6ea9218f40febe06ba2f03bc678d`) for the UI baseline.
- `.planning/REQUIREMENTS.md` — Explicitly defines the allowed interval values: `1, 5, 15, 30, 60, 240, 1440, 10080, 21600` and proxy expectations (FR5).
- `.planning/ROADMAP.md` — Phase 2 tasks: Pass parameter in Express proxy, update `useMarketData.ts`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `web/src/hooks/useMarketData.ts`: Already accepts an `intervalMinutes` parameter and appends it to the API URL.
- `web/server/routes/proxy.js`: Uses `http-proxy-middleware`, which automatically forwards query parameters.

### Established Patterns
- Monorepo execution using `concurrently` (defined in `package.json`).
- Tailwind CSS and Vite for the React frontend styling and building.

### Integration Points
- `web/src/pages/Dashboard.tsx` needs to be updated to pass the selected interval to the `useMarketData` hook.
- `web/src/components/TradingDashboard/` or equivalent UI component where the toggle button group will be placed above the chart.

</code_context>

<specifics>
## Specific Ideas

- Ensure the Toggle Button Group incorporates styling consistent with the Stitch project "Forex Predictor Dashboard". The labels could use standard trading abbreviations like "15m", "1H", "4H", "1D" mapped to their respective minute values (15, 60, 240, 1440).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-express-frontend-updates*
*Context gathered: 2026-04-19*
