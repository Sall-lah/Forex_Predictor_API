---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true
requirements: [FRONTEND-BACKEND-INTERVAL]
must_haves:
  truths:
    - User can select an interval (1, 5, 15, 30, 60, 240, 1440, 10080, 21600) on the frontend
    - Backend accepts this interval and forwards it to the Kraken API
  artifacts:
    - path: api/app/shared/ohlcv/kraken_api.py
      provides: "Accepts interval param in fetch method"
    - path: web/src/App.tsx # Or equivalent main UI component
      provides: "Interval selector UI"
  key_links:
    - from: frontend UI
      to: backend API
      via: HTTP request parameter
    - from: backend API
      to: Kraken API
      via: HTTP request parameter
---

<objective>
Update the application to allow dynamic interval selection for Kraken API data fetching.

Purpose: Instead of fetching with a hardcoded default interval, the frontend will allow users to select from a predefined list of intervals [1, 5, 15, 30, 60, 240, 1440, 10080, 21600] and pass it to the backend. The backend will use this parameter when calling the Kraken API.
Output: Backend endpoints and Kraken client updated to accept the interval parameter; Frontend UI updated with a selector to pass this parameter.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
# Relevant files to update:
@api/app/shared/ohlcv/kraken_api.py
@api/app/features/prediction/router.py
@api/app/features/historic_data/router.py
@api/app/features/prediction/service.py
@api/app/features/historic_data/service.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update Backend to Accept Interval Parameter</name>
  <files>api/app/shared/ohlcv/kraken_api.py, api/app/features/prediction/router.py, api/app/features/historic_data/router.py, api/app/features/prediction/service.py, api/app/features/historic_data/service.py</files>
  <action>
    1. Update `KrakenAPIClient` in `api/app/shared/ohlcv/kraken_api.py` to accept an `interval` parameter (type `int`, default `1`) in its fetch method, and append it as `interval=X` to the Kraken API request params.
    2. Update the router endpoints in `api/app/features/prediction/router.py` and `api/app/features/historic_data/router.py` to accept an optional `interval` query parameter. Validate that it is one of: `[1, 5, 15, 30, 60, 240, 1440, 10080, 21600]`.
    3. Update the corresponding `Service` classes to accept this interval parameter from the router and pass it down to the `KrakenAPIClient` fetch calls.
  </action>
  <verify>
    <automated>pytest api/tests -k "kraken or router or service"</automated>
  </verify>
  <done>Backend successfully receives the interval parameter and forwards it to the Kraken API.</done>
</task>

<task type="auto">
  <name>Task 2: Update Frontend to Include Interval Selector</name>
  <files>web/src/App.tsx, web/src/components/Dashboard.tsx</files>
  <action>
    1. Locate the main React component responsible for making the API calls to the backend (e.g., `Dashboard.tsx` or `App.tsx` in `web/src/`).
    2. Add a state variable for `interval` with a default value of `1`.
    3. Add a UI selector (e.g., `<select>` or a button group) allowing the user to choose an interval from `[1, 5, 15, 30, 60, 240, 1440, 10080, 21600]`. Add appropriate labels (e.g., "1m", "5m", "1h", "4h", "1d", etc.).
    4. Update the `fetch` or `axios` call that targets the backend API to append the selected interval as a query parameter (e.g., `?interval=${interval}`).
  </action>
  <verify>
    <automated>cd web && npm run lint</automated>
  </verify>
  <done>Frontend displays an interval selector and passes the selected value to the backend API.</done>
</task>

</tasks>

<success_criteria>
- Backend validates and uses the interval parameter when calling Kraken API.
- Frontend includes a selector for the interval and sends it with API requests.
- The interval parameter correctly defaults to 1 if not provided.
</success_criteria>

<output>
After completion, create `.planning/quick/260419-frontend-backend-interval/quick-01-SUMMARY.md`
</output>
