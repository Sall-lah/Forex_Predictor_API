"""Token bucket implementation with continuous refill behavior."""

import math
import time
from collections.abc import Callable

from app.middleware.rate_limit.schemas import (
    RateLimitDecision,
    RateLimitPolicy,
    RateLimitState,
)


class TokenBucket:
    """Per-request token bucket calculator producing stable decision metadata."""

    def __init__(self, now_func: Callable[[], float] | None = None) -> None:
        self._now_func = now_func or time.monotonic

    def consume(
        self,
        state: RateLimitState | None,
        policy: RateLimitPolicy,
    ) -> tuple[RateLimitDecision, RateLimitState]:
        """Consume one token if available and return decision plus updated state."""
        now = self._now_func()
        resolved_state = state or RateLimitState(
            tokens=float(policy.capacity),
            last_refill_at=now,
        )

        elapsed = max(0.0, now - resolved_state.last_refill_at)
        refilled_tokens = min(
            float(policy.capacity),
            resolved_state.tokens + (elapsed * policy.refill_rate_per_second),
        )

        if refilled_tokens >= 1.0:
            remaining_tokens = refilled_tokens - 1.0
            updated_state = RateLimitState(tokens=remaining_tokens, last_refill_at=now)
            reset_after_seconds = self._seconds_until_next_token(
                tokens=remaining_tokens,
                capacity=policy.capacity,
                refill_rate=policy.refill_rate_per_second,
            )
            decision = RateLimitDecision(
                allowed=True,
                limit=policy.capacity,
                remaining=max(0, int(math.floor(remaining_tokens))),
                reset_after_seconds=reset_after_seconds,
                retry_after_seconds=None,
            )
            return decision, updated_state

        updated_state = RateLimitState(tokens=refilled_tokens, last_refill_at=now)
        retry_after_seconds = self._seconds_until_next_token(
            tokens=refilled_tokens,
            capacity=policy.capacity,
            refill_rate=policy.refill_rate_per_second,
        )
        decision = RateLimitDecision(
            allowed=False,
            limit=policy.capacity,
            remaining=0,
            reset_after_seconds=retry_after_seconds,
            retry_after_seconds=retry_after_seconds,
        )
        return decision, updated_state

    @staticmethod
    def _seconds_until_next_token(
        tokens: float, capacity: int, refill_rate: float
    ) -> int:
        """Calculate rounded-up wait until either next token or full reset."""
        if tokens >= float(capacity):
            return 0

        missing = max(0.0, 1.0 - tokens)
        if missing <= 0.0:
            return 0

        return int(math.ceil(missing / refill_rate))
