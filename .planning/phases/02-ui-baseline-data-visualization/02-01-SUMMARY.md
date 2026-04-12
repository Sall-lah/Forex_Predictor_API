---
phase: 02-ui-baseline-data-visualization
plan: 01
subsystem: web
tags:
  - React
  - UI
  - Dashboard
  - Template
requires: []
provides:
  - Dashboard UI Baseline
  - Chart Component placeholder
affects:
  - web/src/App.tsx
  - web/src/components/Dashboard.tsx
  - web/src/components/Chart.tsx
  - web/package.json
tech-stack:
  added:
    - lightweight-charts
  patterns:
    - React Functional Components
key-files:
  created:
    - web/src/components/Dashboard.tsx
    - web/src/components/Chart.tsx
  modified:
    - web/package.json
    - web/src/App.tsx
key-decisions:
  - Extracted the main `<main>` container from the Stitch HTML export into `Dashboard.tsx`
  - Created a dedicated `Chart.tsx` component to wrap the lightweight-charts instance (currently a placeholder)
metrics:
  duration: 5 minutes
  completed: 2026-04-12
---

# Phase 02 Plan 01: Scaffold UI Baseline Summary

Integrated the "Forex Dashboard with SL/TP Controls" Stitch template and added lightweight-charts dependency.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Unblocking] Migrated HTML to React JSX syntax**
- **Found during:** Task 2
- **Issue:** Downloaded template was raw HTML and not a React component
- **Fix:** Processed HTML through regex to convert `class` to `className`, `for` to `htmlFor`, fix SVG properties (`strokeWidth`, `strokeDasharray`, `viewBox`, `preserveAspectRatio`), map inline CSS, and self-close void tags. Injected `<Chart />` component in the main graph space.
- **Files modified:** `web/src/components/Dashboard.tsx`
- **Commit:** `50756e9`

**2. [Rule 1 - Bug] Unused React import in App.tsx breaking build**
- **Found during:** Task 2 verification (`npm run build`)
- **Issue:** `React` was imported but never read, causing TS6133
- **Fix:** Removed unused `import React from 'react'` from `App.tsx`
- **Files modified:** `web/src/App.tsx`
- **Commit:** `50756e9`

## Known Stubs

- **Chart Placeholder:** `web/src/components/Chart.tsx` (Line 6) currently only renders the styled container div; it is mocked out waiting for `lightweight-charts` actual initialization in the next plan.
- **Data Mocking:** Dashboard currently holds all the template mock values instead of actual state. It will be wired to actual data later.

## Self-Check: PASSED
- `web/package.json` contains `lightweight-charts`
- `web/src/components/Dashboard.tsx` created and exports `Dashboard` component
- `web/src/components/Chart.tsx` created and exports `Chart` component
- `web/src/App.tsx` modified to use `Dashboard`
- Builds without errors: `npm run build`

## Commits
- `78479ac` chore(02-01): install lightweight-charts in web
- `50756e9` feat(02-01): download and integrate Stitch Dashboard template
