---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - web/package.json
  - web/src/hooks/useMarketData.ts
  - web/src/components/Chart.tsx
autonomous: true
requirements:
  - REFACTOR-REACT-NO-USEEFFECT
must_haves:
  truths:
    - Market data is fetched and polled without useEffect
    - Chart initializes and updates without useEffect
    - No useEffect imports exist in the React codebase
  artifacts:
    - path: web/src/hooks/useMarketData.ts
      provides: Data fetching logic
    - path: web/src/components/Chart.tsx
      provides: UI component logic
  key_links:
    - from: web/src/components/Chart.tsx
      to: lightweight-charts
      via: Callback Ref pattern for initialization
---

<objective>
Refactor the React codebase so it does not use `useEffect` anywhere, replacing data fetching with SWR and chart lifecycle with the callback ref pattern.
</objective>

<context>
@.planning/STATE.md
@web/src/hooks/useMarketData.ts
@web/src/components/Chart.tsx
</context>

<tasks>

<task type="auto">
  <name>Task 1: Install SWR and refactor data fetching</name>
  <files>web/package.json, web/src/hooks/useMarketData.ts</files>
  <action>
    Run `npm install swr` inside `web/`.
    Refactor `web/src/hooks/useMarketData.ts` to use `useSWR` for polling the historic data endpoint instead of `useEffect` + `setInterval`.
    Remove `useEffect` import and usage. Handle the response parsing similarly (mapping API records to OHLCVData format) within the SWR fetcher function. Ensure the polling interval is set via SWR's `refreshInterval` option.
  </action>
  <verify>
    <automated>cd web && npm ls swr && grep -L "useEffect" src/hooks/useMarketData.ts</automated>
  </verify>
  <done>SWR handles the polling and useMarketData.ts no longer imports or uses useEffect.</done>
</task>

<task type="auto">
  <name>Task 2: Refactor Chart component lifecycle</name>
  <files>web/src/components/Chart.tsx</files>
  <action>
    Refactor `Chart.tsx` to completely remove `useEffect`. 
    Use a `useCallback` ref for the chart container element to initialize the lightweight chart when the node mounts, and to clean it up when the node unmounts. 
    To handle `data` prop updates without `useEffect`, use a combination of a mutable ref to hold the initialized `series` and a render-phase or memoized check to call `series.setData()` when the `data` array reference changes.
    Remove `useEffect` import from React.
  </action>
  <verify>
    <automated>cd web && grep -L "useEffect" src/components/Chart.tsx</automated>
  </verify>
  <done>Chart.tsx no longer uses useEffect but still initializes, resizes, and renders candlestick data correctly.</done>
</task>

</tasks>

<success_criteria>
The string "useEffect" is entirely absent from `web/src/components/Chart.tsx` and `web/src/hooks/useMarketData.ts`. The chart still draws and polling still fetches.
</success_criteria>

<output>
After completion, create `.planning/quick/260419-erg-refactor-react-so-it-does-not-use-any-us/quick-1-SUMMARY.md`
</output>