# Forex Predictor Frontend & Monorepo Integration

## What This Is

This project adds a React and Express frontend inside a new `/web/` directory to the existing Forex Predictor API. It unifies the application into a monorepo structure with a single script to concurrently run both the API bot and the web server.

## Core Value

A unified, easily runnable Forex trading dashboard that combines the existing backend prediction engine with a new React-based user interface.

## Requirements

### Validated

- ✓ API serves prediction inference from Kraken OHLCV data through `/api/v1/prediction/predict` — existing
- ✓ API serves live historic OHLCV data through `/api/v1/historic-data/live` — existing

### Active

- [ ] Create a frontend application in the `/web/` directory
- [ ] Use React for the frontend UI
- [ ] Use Express for the frontend server/API gateway
- [ ] Create a unified startup script to run both the FastAPI backend and the Express web server concurrently
- [ ] Use Stitch project "Forex Predictor Dashboard"
- [ ] Use "Forex Dashboard with SL/TP Controls" as the frontend template
- [ ] Ensure seamless integration between the frontend UI and existing API endpoints

### Out of Scope

- Changes to the existing ML model or core backend logic — focusing on frontend integration and monorepo startup orchestration

## Context

The repository currently contains an operational FastAPI backend in `api/` that makes predictions using LightGBM. The goal is to extend this into a full application by adding a React/Express frontend in `web/`. The user specifically wants to leverage Context7 MCPs for documentation and Stitch UI assets ("Forex Predictor Dashboard" project, "Forex Dashboard with SL/TP Controls" screen) for the frontend design. 

## Constraints

- **Tech Stack:** Must use React and Express for the frontend.
- **Monorepo Execution:** Must provide a single command/script to boot both the `api/` bot and the `web/` server together.
- **Template constraints:** Must use the specified Stitch project and screen for the UI baseline.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Monorepo layout with unified runner | Reduces developer friction and simplifies local startup | — Pending |
| React + Express for web layer | User requested stack, common and well-supported pattern | — Pending |
| Stitch UI template | User requested specific design baseline | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-12 after initialization*