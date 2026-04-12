---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - web/src/hooks/useMarketData.ts
autonomous: true
requirements: [FIX-FETCH]
must_haves:
  truths:
    - Frontend fetches candlestick data successfully without 422 errors
  artifacts:
    - path: web/src/hooks/useMarketData.ts
      provides: Data fetching hook with correct pair parameter
  key_links:
    - from: web/src/hooks/useMarketData.ts
      to: backend API
      via: query parameter `?pair=BTC/USD`
---

<objective>
Fix the current fetching issue by ensuring the frontend provides the required `pair` query parameter to the backend.
Purpose: The backend HistoricData API expects a `pair` query parameter. Omitting it causes a 422 Validation Error, leading to connection lost.
Output: Fixed `useMarketData.ts` hook.
</objective>

<context>
@web/src/hooks/useMarketData.ts
@web/CANDLEDATAFETCHRESULT.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add pair parameter to fetch</name>
  <files>web/src/hooks/useMarketData.ts</files>
  <action>
    Modify `useMarketData` to accept an optional `pair` string argument (defaulting to `'BTC/USD'`). Update the `fetch` URL to include this parameter: `fetch('/api/v1/historic-data/live?pair=' + encodeURIComponent(pair))`. Keep the mapping logic for `result.data` unchanged as it correctly parses the structure shown in `web/CANDLEDATAFETCHRESULT.md`.
  </action>
  <verify>
    <automated>cd web && npm run build</automated>
  </verify>
  <done>The frontend passes the `pair` query parameter, avoiding 422 validation errors.</done>
</task>

</tasks>

<success_criteria>
The frontend correctly initiates fetches to `/api/v1/historic-data/live?pair=BTC/USD` preventing API rejections.
</success_criteria>

<output>
After completion, create `.planning/quick/260412-spd-link-frontend-and-backend-data-candle-pr/quick-01-SUMMARY.md`
</output>