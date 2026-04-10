"""Tests for rate-limit schemas and token bucket behavior."""

import pytest
from pydantic import ValidationError

from app.middleware.rate_limit.bucket import TokenBucket
from app.middleware.rate_limit.schemas import RateLimitDecision, RateLimitPolicy


class FakeClock:
    """Controllable monotonic clock helper for deterministic tests."""

    def __init__(self, initial: float) -> None:
        self._now = initial

    def now(self) -> float:
        """Return current monotonic time."""
        return self._now

    def advance(self, seconds: float) -> None:
        """Advance clock by fixed amount."""
        self._now += seconds


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


def test_bucket_refill_restores_capacity_after_wait() -> None:
    """Elapsed time should restore enough tokens to allow a later request."""
    clock = FakeClock(initial=100.0)
    bucket = TokenBucket(now_func=clock.now)
    policy = RateLimitPolicy(capacity=2, refill_rate_per_second=0.5)

    first, state = bucket.consume(state=None, policy=policy)
    second, state = bucket.consume(state=state, policy=policy)
    denied, state = bucket.consume(state=state, policy=policy)

    clock.advance(2.1)
    after_refill, state = bucket.consume(state=state, policy=policy)

    assert first.allowed is True
    assert second.allowed is True
    assert denied.allowed is False
    assert denied.retry_after_seconds is not None
    assert after_refill.allowed is True
    assert state.tokens >= 0.0


def test_bucket_denied_decision_reports_positive_retry_and_reset() -> None:
    """Denied decisions should include positive retry/reset timing values."""
    clock = FakeClock(initial=200.0)
    bucket = TokenBucket(now_func=clock.now)
    policy = RateLimitPolicy(capacity=1, refill_rate_per_second=0.25)

    _allowed, state = bucket.consume(state=None, policy=policy)
    denied, _ = bucket.consume(state=state, policy=policy)

    assert denied.allowed is False
    assert denied.retry_after_seconds is not None
    assert denied.retry_after_seconds > 0
    assert denied.reset_after_seconds == denied.retry_after_seconds


def test_bucket_allows_exactly_capacity_requests_in_burst() -> None:
    """Within-burst requests should allow up to configured capacity only."""
    clock = FakeClock(initial=300.0)
    bucket = TokenBucket(now_func=clock.now)
    policy = RateLimitPolicy(capacity=4, refill_rate_per_second=1.0)

    state = None
    decisions: list[RateLimitDecision] = []
    for _ in range(5):
        decision, state = bucket.consume(state=state, policy=policy)
        decisions.append(decision)

    assert [decision.allowed for decision in decisions] == [
        True,
        True,
        True,
        True,
        False,
    ]
    assert decisions[-1].remaining == 0


def test_bucket_partial_refill_keeps_deny_until_one_full_token() -> None:
    """Partial refill under one token should still deny the next request."""
    clock = FakeClock(initial=400.0)
    bucket = TokenBucket(now_func=clock.now)
    policy = RateLimitPolicy(capacity=1, refill_rate_per_second=0.5)

    _allowed, state = bucket.consume(state=None, policy=policy)
    denied_initial, state = bucket.consume(state=state, policy=policy)
    clock.advance(1.0)
    denied_partial, state = bucket.consume(state=state, policy=policy)
    clock.advance(1.1)
    allowed_after_full, _ = bucket.consume(state=state, policy=policy)

    assert denied_initial.allowed is False
    assert denied_partial.allowed is False
    assert denied_partial.retry_after_seconds is not None
    assert allowed_after_full.allowed is True
