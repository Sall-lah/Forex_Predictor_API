---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - api/.env
  - api/.env.example
  - api/tests/
autonomous: true
requirements: []
must_haves:
  truths:
    - Pydantic Settings no longer throws ValidationError for KRAKEN_DEFAULT_HOURS or PREDICTION_FETCH_HOURS
    - pytest runs cleanly without any configuration errors
  artifacts:
    - path: api/.env
      provides: Valid environment variables configuration
    - path: api/.env.example
      provides: Template for environment variables
  key_links: []
---

<objective>
Fix `pydantic_core._pydantic_core.ValidationError` caused by extra environment variables `KRAKEN_DEFAULT_HOURS` and `PREDICTION_FETCH_HOURS` that are still present in `.env` and `.env.example` after being removed from `api/app/core/config.py`.

Purpose: Prevent server and test crash loops due to Pydantic Settings throwing an error with `extra='forbid'`.
Output: Clean `.env` and `.env.example` files, and passing tests.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@api/app/core/config.py
@api/.env.example
</context>

<tasks>

<task type="auto">
  <name>Task 1: Clean up environment files</name>
  <files>api/.env, api/.env.example</files>
  <action>Open `api/.env` and `api/.env.example` and completely remove any lines defining or referencing `KRAKEN_DEFAULT_HOURS` and `PREDICTION_FETCH_HOURS`.</action>
  <verify>
    <automated>! grep -q "KRAKEN_DEFAULT_HOURS\|PREDICTION_FETCH_HOURS" api/.env api/.env.example</automated>
  </verify>
  <done>The forbidden environment variables no longer exist in the .env files.</done>
</task>

<task type="auto">
  <name>Task 2: Remove references in tests or config</name>
  <files>api/tests/</files>
  <action>Search the `api/tests` directory (and any other configuration files like pytest.ini) for `KRAKEN_DEFAULT_HOURS` and `PREDICTION_FETCH_HOURS`. If any mock or patch uses them, remove or replace those references.</action>
  <verify>
    <automated>! grep -r "KRAKEN_DEFAULT_HOURS\|PREDICTION_FETCH_HOURS" api/tests/</automated>
  </verify>
  <done>No references to the removed environment variables remain in the test suite.</done>
</task>

<task type="auto">
  <name>Task 3: Verify the fix with tests</name>
  <files>api/pytest.ini</files>
  <action>Run the full pytest suite in the `api` directory to ensure that the Pydantic ValidationError is resolved and no tests are failing as a result.</action>
  <verify>
    <automated>cd api && pytest</automated>
  </verify>
  <done>The test suite runs and passes completely without Pydantic validation errors.</done>
</task>

</tasks>

<success_criteria>
- `api/.env` and `api/.env.example` do not contain `KRAKEN_DEFAULT_HOURS` or `PREDICTION_FETCH_HOURS`.
- Running `pytest` in `api/` succeeds without `pydantic_core._pydantic_core.ValidationError`.
</success_criteria>
