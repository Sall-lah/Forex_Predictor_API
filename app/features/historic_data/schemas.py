"""
Pydantic schemas for Historic Data feature.

Models:
- OHLCVRecord: Single candlestick data point
- HistoricDataRequest: Request payload for processing OHLCV data
- HistoricDataResponse: Response with OHLCV records
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class OHLCVRecord(BaseModel):
    """
    Single OHLCV (Open-High-Low-Close-Volume) candlestick record.

    Represents price and volume data for a specific time period.
    All price fields must be positive; volume must be non-negative.
    """

    timestamp: datetime = Field(
        ...,
        description="UTC timestamp for candle start time",
        examples=["2026-03-23T14:00:00Z"],
    )
    open: float = Field(
        ...,
        description="Opening price",
        gt=0,
    )
    high: float = Field(
        ...,
        description="Highest price in period",
        gt=0,
    )
    low: float = Field(
        ...,
        description="Lowest price in period",
        gt=0,
    )
    close: float = Field(
        ...,
        description="Closing price",
        gt=0,
    )
    volume: float = Field(
        ...,
        description="Trade volume in period",
        ge=0,
    )


class HistoricDataRequest(BaseModel):
    """
    Request for processing OHLCV data.

    Contains symbol identifier and list of OHLCV records to process.
    """

    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading pair symbol (e.g., 'BTC/USD')",
        examples=["BTC/USD"],
    )
    records: List[OHLCVRecord] = Field(
        ...,
        min_length=1,
        description="OHLCV candles ordered by time (oldest first)",
    )


class HistoricDataResponse(BaseModel):
    """
    Response containing historic OHLCV data.

    Includes symbol, record count, and the actual OHLCV data.
    """

    symbol: str = Field(
        ...,
        description="Trading pair symbol",
    )
    total_records: int = Field(
        ...,
        description="Number of OHLCV records",
    )
    data: List[OHLCVRecord] = Field(
        ...,
        description="OHLCV candlestick records",
    )
