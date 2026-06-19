"""
Pydantic schemas for Subscriptions feature.

Models:
- SubscriptionPair: Single pair with its intervals
- SubscriptionResponse: Response with all configured subscriptions
"""

from pydantic import BaseModel, Field


class SubscriptionPair(BaseModel):
    """
    A trading pair and the OHLC intervals the frontend should subscribe to.
    """

    pair: str = Field(
        ...,
        description="Trading pair symbol",
        examples=["BTC/USD"],
    )
    intervals: list[int] = Field(
        ...,
        description="OHLC interval minutes to subscribe to",
        examples=[[1, 5, 15, 60, 240]],
    )


class SubscriptionResponse(BaseModel):
    """
    Response containing all configured trading pair subscriptions.

    The frontend uses this to know which Kraken WS channels to open.
    """

    subscriptions: list[SubscriptionPair] = Field(
        ...,
        description="Configured trading pair subscriptions",
    )
