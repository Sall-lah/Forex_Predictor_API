# Project State

## Project Reference

**Core Value**: A unified, easily runnable Forex trading dashboard that combines the existing backend prediction engine with a new React-based user interface.
**Current Focus**: Monorepo Foundation & Orchestration

## Current Position

**Phase**: 1 - Foundation & Orchestration
**Plan**: None
**Status**: Not Started

## Progress

```text
Phases:    [                                                  ] 0/3 (0%)
Plans:     [                                                  ] 0/0 (0%)
```

## Accumulated Context

### Decisions
- Adopt a Backend-For-Frontend (BFF) proxy pattern to sidestep CORS.
- Use concurrently and npm workspaces for a lightweight monorepo runner.
- Leverage Vite for React and Express 5.0 for the server layer.

### Blockers
- None currently.

### Session Continuity
- Ensure proper process termination (SIGINT handling) is tested early when building the root runner script.
