"""Thread-safe in-memory storage for rate-limit bucket state."""

import asyncio

from app.middleware.rate_limit.schemas import RateLimitState


class InMemoryRateLimitStorage:
    """Stores bucket state per key with atomic async operations."""

    def __init__(self, max_entries: int, ttl_seconds: int) -> None:
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._states: dict[str, RateLimitState] = {}
        self._order: list[str] = []
        self._lock = asyncio.Lock()

    async def get_state(self, key: str) -> RateLimitState | None:
        """Fetch current state for a key if present."""
        async with self._lock:
            return self._states.get(key)

    async def upsert_state(self, key: str, state: RateLimitState) -> None:
        """Insert or replace state atomically and enforce max-entry bound."""
        async with self._lock:
            is_new = key not in self._states

            if is_new:
                self._order.append(key)
            self._states[key] = state

            while len(self._states) > self._max_entries and self._order:
                oldest_key = self._order.pop(0)
                if oldest_key in self._states:
                    del self._states[oldest_key]

    async def delete_state(self, key: str) -> None:
        """Delete state for a key when present."""
        async with self._lock:
            self._states.pop(key, None)
            self._order = [
                existing_key for existing_key in self._order if existing_key != key
            ]

    async def cleanup_expired(self, now_monotonic: float) -> int:
        """Remove entries whose last refill age exceeds configured TTL."""
        async with self._lock:
            keys_to_remove = [
                key
                for key, state in self._states.items()
                if now_monotonic - state.last_refill_at > self._ttl_seconds
            ]

            for key in keys_to_remove:
                del self._states[key]

            if keys_to_remove:
                removed_set = set(keys_to_remove)
                self._order = [key for key in self._order if key not in removed_set]

            return len(keys_to_remove)
