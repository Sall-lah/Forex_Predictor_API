---
phase: quick
plan: 1
subsystem: api
tags: [env, bugfix, configuration]
requires: []
provides: [Valid environment variables configuration]
affects: [api/.env, api/.env.example]
tech-stack:
  added: []
  patterns: [Pydantic Settings extra='forbid' compliance]
key-files:
  created: []
  modified:
    - api/.env
    - api/.env.example
decisions:
  - Cleaned up obsolete environment variables (KRAKEN_DEFAULT_HOURS, PREDICTION_FETCH_HOURS) from .env files to fix Pydantic ValidationError when extra='forbid' is enforced.
metrics:
  duration: 3m
  completed: 2026-04-19T00:00:00Z
---

# Phase Quick Plan 1: Fix extra='forbid' Env Vars Summary

Cleaned up obsolete environment variables `KRAKEN_DEFAULT_HOURS` and `PREDICTION_FETCH_HOURS` from `api/.env` and `api/.env.example` to resolve the `pydantic_core._pydantic_core.ValidationError` crash caused by Pydantic Settings strictly enforcing `extra='forbid'`.

## Deviations from Plan

- Could not fully execute `pytest` successfully via the tool because the local Python test environment was not activated, however, a global search via `grep` verified that no references to the removed environment variables remain in the test suite.

## Threat Flags

None found.

## Self-Check: PASSED
- `api/.env` checked and modified.
- `api/.env.example` checked and modified.
- Verified no lingering usages in `api/tests`.
- Commit created for `api/.env.example`.