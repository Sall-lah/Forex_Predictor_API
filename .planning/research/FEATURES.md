# Feature Landscape

**Domain:** Forex Trading Dashboard (React/Express + Python API)
**Researched:** 2026-04-12

## Table Stakes

Features users expect in any functional trading dashboard. Missing = product feels incomplete and unusable for active trading or analysis.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Live Price Chart (OHLCV)** | Traders cannot make decisions without visualizing historical and live price action. | High | Must render candlestick charts using data from `/historic-data/live`. TradingView's Lightweight Charts is the industry standard. |
| **Current Market Price Display** | Instant visibility into the current bid/ask or mid-price is the most basic requirement. | Low | Top of dashboard, large font, color-coded for up/down movement. |
| **Prediction Overlay / Status** | The core value prop of this specific app. Users need to see what the LightGBM model predicts next. | Medium | Rendered alongside or overlaid on the chart, pulling from `/prediction/predict`. |
| **Stop Loss (SL) & Take Profit (TP) Inputs** | Essential risk management. Traders must define exit conditions before entering a trade. | Medium | Typically input fields (price or pips/%) with visual slider or chart lines. |
| **API Connectivity Status** | Users need to know if the backend Python API or exchange (Kraken) connection is active/stale. | Low | Simple indicator (Green/Red dot) showing WebSocket or polling health. |

## Differentiators

Features that set this product apart from standard exchange UIs. Not strictly required for V1, but highly valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Visual SL/TP Dragging on Chart** | Vastly improves UX over manual text entry. Users can visually set risk boundaries based on chart support/resistance. | High | Requires bidirectional sync between chart library and React state. |
| **Prediction Confidence Gauge** | Shows *how* certain the LightGBM model is, allowing traders to adjust position sizing based on conviction. | Medium | If the API exposes probability, a visual gauge/meter adds massive value. |
| **Backtest Simulation Overlay** | Showing how previous predictions would have performed against actual historic data builds trust in the model. | High | Requires fetching historic predictions and plotting win/loss markers. |
| **Dynamic SL/TP Recommendations** | Using the model's volatility metrics to suggest optimal SL/TP widths rather than manual entry. | High | Requires backend support for ATR or volatility-based suggestions. |

## Anti-Features

Features to explicitly NOT build to maintain scope and stability.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Direct Order Execution / Wallet Management** | Out of scope for a prediction dashboard. Security risks and massive regulatory/liability overhead. | Build a purely informational/analytical dashboard. Output signal webhooks instead. |
| **Multi-Exchange Aggregation** | The backend is currently hardcoded for Kraken. Adding Binance/Oanda etc. breaks the existing backend scope. | Stick to the existing Kraken data pipeline. |
| **Social Trading / Chat** | Distraction from the core value proposition (AI prediction). | Focus purely on single-user technical analysis and risk management. |

## Feature Dependencies

```text
Live Price Chart → Prediction Overlay (Chart must exist to overlay signals)
Live Price Chart → Visual SL/TP Dragging (Requires chart coordinate mapping)
Current Market Price → SL/TP Inputs (Inputs often calculated as +/- % from current price)
```

## MVP Recommendation

Prioritize for Phase 1:
1. Live Price Chart (fetching from `/api/v1/historic-data/live`)
2. Current Market Price Display
3. Standard Text/Number Inputs for SL/TP Controls
4. Basic Prediction Status Indicator (from `/api/v1/prediction/predict`)

Defer to Phase 2: Visual SL/TP dragging, Prediction Confidence Gauge, Dynamic SL/TP recommendations.

## Sources

- Project Context (`.planning/PROJECT.md`)
- Established trading UX patterns (TradingView, MetaTrader)
- High confidence based on standard trading UI requirements.