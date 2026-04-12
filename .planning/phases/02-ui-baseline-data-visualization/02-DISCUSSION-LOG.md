# Phase 2: UI Baseline & Data Visualization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-12
**Phase:** 2-UI Baseline & Data Visualization
**Areas discussed:** Charting Library, API Polling Strategy, Error Handling

---

## Charting Library

| Option | Description | Selected |
|--------|-------------|----------|
| Lightweight Charts (Recommended) | High performance, built by TradingView specifically for financial data and OHLCV | o" |
| ApexCharts | Feature rich, interactive, but slightly heavier | |
| Recharts | Simple React charting library, but requires custom candlestick implementation | |

**User's choice:** Lightweight Charts (Recommended)
**Notes:** 

---

## API Polling Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Frequent Polling (1-5s) (Recommended) | Poll every 1-5 seconds to keep the chart live without overwhelming the REST API | o" |
| Moderate Polling (10-30s) | Poll every 10-30 seconds to reduce load, suitable for longer timeframes | |
| WebSockets (requires backend change) | Upgrade backend to WebSocket for real-time pushing | |

**User's choice:** Frequent Polling (1-5s) (Recommended)
**Notes:** 

---

## Error Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Status indicator + Warning overlay (Recommended) | Change header indicator to red, keep chart visible but show a non-intrusive 'stale data' warning overlay. | o" |
| Blocking Overlay | Show a full-screen or full-chart blocking error message until connection returns. | |
| Subtle Header Dot Only | Only change a small status dot in the header without disrupting the view. | |

**User's choice:** Status indicator + Warning overlay (Recommended)
**Notes:** 

---

## the agent's Discretion

None

## Deferred Ideas

None
