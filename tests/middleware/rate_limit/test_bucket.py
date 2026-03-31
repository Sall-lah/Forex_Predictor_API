"""Tests for rate-limit schemas and token bucket behavior."""

import pytest
from pydantic import ValidationError

from app.middleware.rate_limit.schemas import RateLimitDecision, RateLimitPolicy


def test_schema_rate_limit_policy_requires_positive_values() -> None:
    """Policy should reject non-positive capacity and refill rate values."""
    with pytest.raises(ValidationError):
        RateLimitPolicy(capacity=0, refill_rate_per_second=1.0)

    with pytest.raises(ValidationError):
        RateLimitPolicy(capacity=10, refill_rate_per_second=0.0)


def test_schema_rate_limit_decision_supports_allow_and_deny() -> None:
    """Decision model should represent both allowed and denied responses."""
    allow_decision = RateLimitDecision(
        allowed=True,
        limit=10,
        remaining=9,
        reset_after_seconds=1,
        retry_after_seconds=None,
    )
    deny_decision = RateLimitDecision(
        allowed=False,
        limit=10,
        remaining=0,
        reset_after_seconds=1,
        retry_after_seconds=6,
    )

    assert allow_decision.allowed is True
    assert allow_decision.retry_after_seconds is None
    assert deny_decision.allowed is False
    assert deny_decision.retry_after_seconds == 6
