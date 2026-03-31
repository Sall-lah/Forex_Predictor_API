"""
Pydantic schemas for Prediction feature.

Models:
- PredictionRequest: Request payload for prediction endpoint
- PredictionResponse: Response containing prediction probability
"""

from typing import Literal

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """
    Request for forex price movement prediction.

    Contains trading pair and asset identifier to fetch data and make prediction.
    """

    pair: str = Field(
        ...,
        min_length=1,
        description="Kraken trading pair (e.g., 'BTC/USD' for BTCUSD)",
        examples=["BTC/USD", "ETH/USD"],
    )
    asset: Literal["BTCUSD", "ETHUSD"] = Field(
        ...,
        description="Asset name for model feature encoding (BTCUSD or ETHUSD)",
        examples=["BTCUSD", "ETHUSD"],
    )


class PredictionResponse(BaseModel):
    """
    Response containing prediction probability.

    Returns the probability that the price will move up (class 1).
    """

    pair: str = Field(
        ...,
        description="Trading pair that was analyzed",
    )
    asset: str = Field(
        ...,
        description="Asset name used for prediction",
    )
    probability_up: float = Field(
        ...,
        description="Probability of upward price movement (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
