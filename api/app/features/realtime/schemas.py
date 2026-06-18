"""
Pydantic schemas for the realtime WebSocket data stream.

Models:
- CandleTick: Canonical candle update broadcast to frontend clients.
- RelaySubscription: Single (pair, interval) tuple for the upstream allowlist.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class CandleTick(BaseModel):
    """
    Single live OHLCV candle tick broadcast over the relay.

    This is the canonical wire format. `timestamp` is the candle start
    expressed as an ISO-8601 UTC datetime so the frontend can reuse its
    existing OHLCVData type without a second type definition.
    """

    pair: str = Field(
        ...,
        description="Trading pair in display form (e.g. 'BTC/USD').",
        examples=["BTC/USD"],
    )
    interval: int = Field(
        ...,
        description="Candle interval in minutes, matches the REST `interval` param.",
        gt=0,
    )
    timestamp: datetime = Field(
        ...,
        description="ISO 8601 UTC datetime marking the start of the candle.",
    )
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: float = Field(..., ge=0)
    is_closed: bool = Field(
        ...,
        description=(
            "False while the candle is still forming, True once the interval "
            "has elapsed and Kraken has closed the bar."
        ),
    )


class RelaySubscription(BaseModel):
    """Static subscription tuple used to configure the upstream client."""

    pair: str
    interval: int = Field(..., gt=0)


class RelayConfigResponse(BaseModel):
    """Snapshot of the active relay subscription allowlist."""

    subscriptions: List[RelaySubscription] = Field(default_factory=list)


class StatusBroadcast(BaseModel):
    """
    Lightweight status message emitted on the WS connection.

    Used by the frontend to detect replay gaps after a reconnect.
    """

    type: str = "status"
    last_successful_tick_at: datetime | None = None
    reconnect_count: int = 0
    kraken_connected: bool = False
