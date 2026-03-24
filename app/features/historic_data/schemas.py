"""
Pydantic schemas for the Historic Data feature.

Why separate schemas for request vs. response: The request defines
what the client sends (query params or body), while the response
defines the exact contract the API guarantees.  Keeping them apart
makes breaking-change detection trivial.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Shared / Embedded Models
# ---------------------------------------------------------------------------

class OHLCVRecord(BaseModel):
    """
    A single OHLCV candlestick record.

    Fields mirror the universal OHLCV format used by most exchange APIs
    (e.g. ccxt, Binance, Yahoo Finance).
    """

    timestamp: datetime = Field(
        ...,
        description="UTC timestamp for the start of the candle.",
        examples=["2026-03-23T14:00:00Z"],
    )
    open: float = Field(..., description="Opening price.", gt=0)
    high: float = Field(..., description="Highest price in the period.", gt=0)
    low: float = Field(..., description="Lowest price in the period.", gt=0)
    close: float = Field(..., description="Closing price.", gt=0)
    volume: float = Field(..., description="Trade volume in the period.", ge=0)


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class HistoricDataRequest(BaseModel):
    """
    Payload for submitting raw OHLCV data for indicator computation.

    Why accept a list in the body rather than fetch internally:
    This keeps the service stateless and lets the caller decide
    the data source (live API, CSV upload, cached DB rows, etc.).
    """

    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading pair symbol, e.g. 'BTC/USD'.",
        examples=["BTC/USD"],
    )
    records: List[OHLCVRecord] = Field(
        ...,
        min_length=1,
        description="Ordered list of OHLCV candles (oldest first).",
    )
    sma_period: Optional[int] = Field(
        default=14,
        gt=0,
        description="Window size for the Simple Moving Average.",
    )
    rsi_period: Optional[int] = Field(
        default=14,
        gt=0,
        description="Window size for the Relative Strength Index.",
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class EnrichedOHLCVRecord(BaseModel):
    """
    An OHLCV record enriched with computed technical indicators.

    Why Optional for indicator fields: The first N-1 rows will have
    NaN values (insufficient lookback), which we serialize as null.
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    sma: Optional[float] = Field(
        default=None,
        description="Simple Moving Average of close price.",
    )
    rsi: Optional[float] = Field(
        default=None,
        description="Relative Strength Index (0-100 scale).",
    )
    macd: Optional[float] = Field(
        default=None,
        description="Moving Average Convergence Divergence (MACD).",
    )
    macd_signal: Optional[float] = Field(
        default=None,
        description="MACD Signal line.",
    )


class HistoricDataResponse(BaseModel):
    """Top-level response wrapper for the historic data endpoint."""

    symbol: str = Field(..., description="The symbol these records belong to.")
    total_records: int = Field(..., description="Number of enriched records returned.")
    data: List[EnrichedOHLCVRecord] = Field(
        ...,
        description="OHLCV records with computed indicators.",
    )
