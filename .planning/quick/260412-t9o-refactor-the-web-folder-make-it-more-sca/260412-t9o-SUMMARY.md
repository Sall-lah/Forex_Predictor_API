---
phase: quick
plan: 260412-t9o
subsystem: "web"
tags: ["refactor", "express", "react", "architecture"]
dependency_graph:
  requires: []
  provides: ["Modular Express BFF", "Scalable React frontend structure"]
  affects: ["web/server", "web/src"]
tech_stack:
  added: []
  patterns: ["Express Routers", "React Pages/Services/Types"]
key_files:
  created: ["web/server/app.js", "web/server/index.js", "web/server/routes/health.js", "web/server/routes/proxy.js", "web/src/pages/Dashboard.tsx", "web/src/services/api.ts", "web/src/types/index.ts"]
  modified: ["web/package.json", "web/src/App.tsx"]
  deleted: ["web/server.js"]
decisions:
  - extracted existing server.js to use standard Express modular routing.
  - moved Dashboard component into pages/ directory and updated App.tsx imports.
  - created shared types interface and API client stub for frontend.
metrics:
  duration_minutes: 2
  tasks_completed: 2
  files_changed: 10
  lines_of_code: 100
  test_coverage_change: 0
---

# Quick Plan 260412-t9o: Refactor the web folder

This quick task reorganized both the Express Backend-For-Frontend (BFF) and the React frontend to establish a scalable architecture.

## Execution Outcomes

- Replaced flat `server.js` with `server/index.js`, `server/app.js` and modular routing.
- Set up standard `pages`, `services`, and `types` directories inside `web/src`.
- Updated `package.json` to properly invoke the new node entrypoint `server/index.js`.
- Migrated the main view from a raw component to `pages/Dashboard.tsx`.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check
- `web/server/index.js` exists.
- `web/src/pages/Dashboard.tsx` exists.
- `App.tsx` correctly imports `Dashboard`.
- TypeScript compiles without errors (`tsc --noEmit`).

## Known Stubs
- `web/src/services/api.ts` is currently a utility file created for use but isn't wired into `useMarketData` yet. This was not strictly required by the tasks but provides the foundation for future data fetching refactors.
