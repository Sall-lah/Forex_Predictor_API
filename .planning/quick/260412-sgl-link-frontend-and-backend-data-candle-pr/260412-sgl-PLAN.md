---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: ["web/src/hooks/useMarketData.ts"]
autonomous: true
requirements: []
must_haves:
  truths:
    - "Chart displays correctly using data fetched from the API"
  artifacts:
    - path: "web/src/hooks/useMarketData.ts"
      provides: "Correctly maps backend API timestamp field to frontend time field"
  key_links:
    - from: "web/src/hooks/useMarketData.ts"
      to: "web/src/components/Chart.tsx"
      via: "OHLCVData mapping"
---

<objective>
Link frontend and backend candle data by standardizing the fetched API payload to match the expected OHLCVData interface.

Purpose: The frontend expects a `time` field in the data payload, but the API returns `timestamp`. This causes data mapping issues when rendering the chart.
Output: Updated `useMarketData.ts` correctly parsing the API payload.
</objective>

<context>
@web/CANDLEDATAFETCHRESULT.md
@web/src/hooks/useMarketData.ts
</context>

<tasks>
<task type="auto">
  <name>Task 1: Map backend timestamp field to OHLCVData</name>
  <files>web/src/hooks/useMarketData.ts</files>
  <action>
    Modify `fetchData` in `useMarketData.ts` to map the `timestamp` field from the backend API response to the `time` field required by `OHLCVData`.
    When parsing the `records` array, use `.map()` to return an array of `OHLCVData` where `time` is set to `record.timestamp || record.time`. Ensure `open`, `high`, `low`, `close`, and `volume` are also correctly mapped from each record.
    Set `data` state with the newly mapped array.
  </action>
  <verify>
    <automated>npm run tsc --prefix web</automated>
  </verify>
  <done>Frontend correctly extracts and normalizes the backend OHLC data.</done>
</task>
</tasks>

<success_criteria>
The frontend candle data payload correctly maps the backend's `timestamp` to `time` without altering UI components.
</success_criteria>
<output>
After completion, verify there are no typescript errors in `web/src/hooks/useMarketData.ts`
</output>