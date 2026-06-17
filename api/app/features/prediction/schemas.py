"""
Pydantic schemas for Prediction feature.

Models:
- PredictionRequest: Request payload for prediction endpoint
- PredictionResponse: Response containing prediction probability
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """
    Request for forex price movement prediction.

    Contains trading pair identifier to fetch data and make prediction.
    """

    pair: str = Field(
        ...,
        min_length=1,
        description="Kraken trading pair (e.g., 'BTC/USD' for BTCUSD)",
        examples=["BTC/USD", "ETH/USD"],
    )


class PredictionResponse(BaseModel):
    """
    Response containing prediction probabilities.

    Returns probabilities for upward, downward, and straight (hold) movement.
    """

    pair: str = Field(
        ...,
        description="Trading pair that was analyzed",
    )
    probability_up: float = Field(
        ...,
        description="Probability of upward price movement in range [0.0, 1.0]",
        ge=0.0,
        le=1.0,
    )
    probability_down: float = Field(
        ...,
        description="Probability of downward price movement in range [0.0, 1.0]",
        ge=0.0,
        le=1.0,
    )
    probability_straight: float = Field(
        ...,
        description="Probability of straight (hold) movement in range [0.0, 1.0]",
        ge=0.0,
        le=1.0,
    )
    computed_at: datetime = Field(
        ...,
        description="Timestamp when the prediction was computed (UTC)",
    )
    valid_until: datetime = Field(
        ...,
        description="Timestamp when the prediction expires and needs recomputation (UTC)",
    )
