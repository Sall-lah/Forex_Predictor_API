"""Tests for rate-limit schemas and token bucket behavior."""

import pytest
from pydantic import ValidationError

from app.middleware.rate_limit.bucket import TokenBucket
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


def test_bucket_consume_allows_when_tokens_available() -> None:
    """Bucket should allow when enough tokens remain."""
    time_values = iter([100.0, 100.0])
    bucket = TokenBucket(now_func=lambda: next(time_values))
    policy = RateLimitPolicy(capacity=2, refill_rate_per_second=1.0)

    decision, new_state = bucket.consume(
        state=None,
        policy=policy,
    )

    assert decision.allowed is True
    assert decision.remaining == 1
    assert decision.retry_after_seconds is None
    assert new_state.tokens == pytest.approx(1.0)


def test_bucket_denies_when_tokens_empty() -> None:
    """Bucket should deny when token balance is insufficient."""
    time_values = iter([200.0, 200.0])
    bucket = TokenBucket(now_func=lambda: next(time_values))
    policy = RateLimitPolicy(capacity=1, refill_rate_per_second=0.5)

    _first_decision, state_after_first = bucket.consume(state=None, policy=policy)
    second_decision, state_after_second = bucket.consume(
        state=state_after_first, policy=policy
    )

    assert second_decision.allowed is False
    assert second_decision.remaining == 0
    assert second_decision.retry_after_seconds is not None
    assert second_decision.retry_after_seconds > 0
    assert state_after_second.tokens == pytest.approx(0.0)


def test_bucket_refills_continuously_up_to_capacity() -> None:
    """Elapsed time should refill tokens continuously and cap at capacity."""
    time_values = iter([300.0, 302.0, 308.0])
    bucket = TokenBucket(now_func=lambda: next(time_values))
    policy = RateLimitPolicy(capacity=3, refill_rate_per_second=0.5)

    _first_decision, state = bucket.consume(state=None, policy=policy)
    _second_decision, state = bucket.consume(state=state, policy=policy)
    third_decision, state = bucket.consume(state=state, policy=policy)

    assert third_decision.allowed is True
    assert state.tokens <= policy.capacity
    assert third_decision.remaining >= 0
