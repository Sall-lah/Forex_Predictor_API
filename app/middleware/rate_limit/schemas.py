"""Typed schemas for rate-limit policies, state, and decisions."""

from pydantic import BaseModel, Field


class RateLimitPolicy(BaseModel):
    """Defines token bucket capacity and refill speed for an endpoint family."""

    capacity: int = Field(gt=0)
    refill_rate_per_second: float = Field(gt=0)


class RateLimitState(BaseModel):
    """Represents persisted token bucket state for a client-endpoint key."""

    tokens: float = Field(ge=0)
    last_refill_at: float = Field(ge=0)


class RateLimitDecision(BaseModel):
    """Decision payload used by middleware to shape headers and responses."""

    allowed: bool
    limit: int = Field(gt=0)
    remaining: int = Field(ge=0)
    reset_after_seconds: int = Field(ge=0)
    retry_after_seconds: int | None = Field(default=None, ge=0)
