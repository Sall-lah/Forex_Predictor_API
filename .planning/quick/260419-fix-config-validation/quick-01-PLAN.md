---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - api/.env
  - api/.env.example
autonomous: true
requirements:
  - CONFIG-FIX-01
must_haves:
  truths:
    - KRAKEN_HOURLY_INTERVAL is removed from environment files
    - Pydantic validation error is fixed
  artifacts:
    - path: api/.env
      provides: Local environment configuration
    - path: api/.env.example
      provides: Example environment configuration
  key_links: []
---

<objective>
Remove `KRAKEN_HOURLY_INTERVAL` from `.env` and `.env.example` to fix the Pydantic validation error caused by `Extra fields not permitted`.
</objective>

<tasks>
<task type="auto">
  <name>Task 1: Clean up environment files</name>
  <files>api/.env, api/.env.example</files>
  <action>Remove any lines defining `KRAKEN_HOURLY_INTERVAL` from `api/.env` and `api/.env.example`. This property was removed from Pydantic `Settings` but might still exist in local configuration files, causing `ValidationError` on startup because `case_sensitive=True` and no extra fields are permitted.</action>
  <verify>
    <automated>cd api; pytest tests/core/test_config.py</automated>
  </verify>
  <done>KRAKEN_HOURLY_INTERVAL is completely removed from both files.</done>
</task>
</tasks>
