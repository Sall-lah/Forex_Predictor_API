---
phase: 01-api-updates
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [
  "api/app/features/historic_data/schemas.py",
  "api/app/features/prediction/schemas.py",
  "api/app/shared/ohlcv/kraken_api.py",
  "api/app/features/historic_data/service.py",
  "api/app/features/prediction/service.py",
  "api/app/features/historic_data/router.py",
  "api/app/features/prediction/router.py"
]
autonomous: true
requirements: ["FR1", "FR2", "FR3"]
must_haves:
  truths:
    - "API accepts an 'interval' query parameter for live data and predictions"
    - "API validates interval against allowed Kraken values [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]"
    - "Kraken API client sends the interval to the Kraken OHLC endpoint"
  artifacts:
    - path: "api/app/shared/ohlcv/kraken_api.py"
      provides: "HTTP client with interval support"
    - path: "api/app/features/historic_data/schemas.py"
      provides: "Request schemas validating interval parameter"
  key_links:
    - from: "api/app/features/prediction/router.py"
      to: "api/app/features/prediction/service.py"
      via: "passing interval arg"
---

<objective>
Update the backend API to support a dynamic timeframe `interval` parameter for fetching OHLCV data from Kraken, and pass it through the routers and services.

Purpose: Allow frontend consumers to request data at different candlestick resolutions (e.g., 5-minute, 1-hour).
Output: Updated backend schemas, services, and routers supporting `interval`.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/REQUIREMENTS.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add interval schemas and update KrakenAPIClient</name>
  <files>
    api/app/features/historic_data/schemas.py,
    api/app/features/prediction/schemas.py,
    api/app/shared/ohlcv/kraken_api.py
  </files>
  <action>
    1. Update `HistoricDataRequest` and `PredictionRequest` schemas (if they exist) or the equivalent schema/query parameters to accept `interval: int = 60` (default 60 mins).
    2. Add validation to ensure `interval` must be one of `[1, 5, 15, 30, 60, 240, 1440, 10080, 21600]`.
    3. Update `KrakenAPIClient` methods (e.g., `fetch_ohlcv`) to accept `interval: int` and append it as `interval={interval}` to the Kraken request parameters.
  </action>
  <verify>
    <automated>pytest api/tests/ -k "kraken or schema" || echo "Test later"</automated>
  </verify>
  <done>Interval parameters are validated by Pydantic and passed through the HTTP client</done>
</task>

<task type="auto">
  <name>Task 2: Wire interval through services and routers</name>
  <files>
    api/app/features/historic_data/service.py,
    api/app/features/prediction/service.py,
    api/app/features/historic_data/router.py,
    api/app/features/prediction/router.py
  </files>
  <action>
    1. Update `HistoricDataService` and `PredictionService` data fetching methods to accept `interval: int` and pass it down to `kraken_client.fetch_ohlcv(...)`.
    2. Update endpoint functions in the routers (`/historic-data/live`, `/prediction/predict`) to accept `interval: int = Query(60, description="...")` or use the Pydantic schema, and pass it to the service calls.
  </action>
  <verify>
    <automated>pytest api/tests/ -k "router or service" || echo "Test later"</automated>
  </verify>
  <done>Endpoint routes pass interval to services, which pass it to the Kraken client</done>
</task>

</tasks>

<verification>
Start the uvicorn server (`uvicorn app.main:app`) and verify the `/docs` UI shows the new `interval` parameter, and requests to `/api/v1/historic-data/live?interval=5` return successfully.
</verification>

<success_criteria>
The FastAPI endpoints for historic data and prediction accept, validate, and utilize the `interval` parameter to fetch dynamic timeframes from Kraken.
</success_criteria>

<output>
After completion, create `.planning/phases/01-api-updates/01-01-SUMMARY.md`
</output>
