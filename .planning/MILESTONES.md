# Milestones

## v1.0: Timeframe Interval Support
**Date:** 2026-04-19
**Status:** Shipped

### Accomplishments
- Added dynamic timeframe interval support to Kraken OHLCV fetches across the API stack.
- Added interval validation and updated Kraken API client to use Pydantic's Literal type for safety.
- Integrated interval selection toggle buttons on the React Dashboard with SWR-driven background loading overlay.
- Preserved default 60-minute interval backward compatibility.

### Known Gaps / Deferred
- Quick Task deferred: 260419-erg-refactor-react-so-it-does-not-use-any-us
- Quick Task deferred: 260419-g0k-refactor-the-react-component-to-use-hook