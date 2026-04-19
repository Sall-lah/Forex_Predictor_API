# Phase 2: Express / Frontend Updates - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-19
**Phase:** 2-Express / Frontend Updates
**Areas discussed:** Transition State, Default Interval, Interval Selector, Proxy Validation

---

## Transition State

| Option | Description | Selected |
|--------|-------------|----------|
| Overlay Spinner (Recommended) | Keep old data visible, overlay a translucent loading spinner (smoother UX) | ✓ |
| Clear & Skeleton | Clear the chart entirely and show a skeleton loader | |
| You decide | Let the agent decide the best approach | |

**User's choice:** Overlay Spinner (Recommended)
**Notes:** Decided for smoother UX.

---

## Default Interval

| Option | Description | Selected |
|--------|-------------|----------|
| 60 minutes (1H) (Recommended) | Preserves backward compatibility and matches the current backend default | ✓ |
| 15 minutes (15M) | More active, finer granularity for trading | |
| 1440 minutes (1D) | Broad overview, good for long-term trends | |
| You decide | Let the agent decide | |

**User's choice:** 60 minutes (1H) (Recommended)
**Notes:** Preserves backward compatibility.

---

## Interval Selector

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle Button Group (Recommended) | Common trading pattern (e.g., [15m] [1H] [4H] [1D]) placed right above the chart | ✓ |
| Dropdown Menu | Conserves space, placed in the top navigation or filter bar | |
| You decide | Let the agent decide | |

**User's choice:** Toggle Button Group (Recommended)
**Notes:** Better trading UI pattern.

---

## Proxy Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Simple Passthrough (Recommended) | FastAPI backend already validates the interval robustly (Phase 1) | ✓ |
| Log Requests | Log interval choices for analytics before forwarding to backend | |
| Validate in Express | Validate the interval in Express before it reaches the backend | |
| You decide | Let the agent decide | |

**User's choice:** Simple Passthrough (Recommended)
**Notes:** Redundant validation not needed.

---

## the agent's Discretion

None

## Deferred Ideas

None
