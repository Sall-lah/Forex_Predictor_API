"""Tests for rate-limit configuration and in-memory storage behavior."""

import asyncio

import pytest

from app.core.config import Settings
from app.middleware.rate_limit.schemas import RateLimitState
from app.middleware.rate_limit.storage import InMemoryRateLimitStorage


def test_config_exposes_default_and_endpoint_rate_limits() -> None:
    """Settings should expose default and per-endpoint limit values."""
    settings = Settings()

    assert settings.RATE_LIMIT_DEFAULT_CAPACITY == 60
    assert settings.RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND == 1.0
    assert settings.RATE_LIMIT_PREDICTION_CAPACITY == 10
    assert settings.RATE_LIMIT_HISTORICAL_CAPACITY == 100


def test_config_exposes_storage_and_proxy_controls() -> None:
    """Settings should expose storage cleanup and trusted proxy controls."""
    settings = Settings()

    assert settings.RATE_LIMIT_STORAGE_MAX_ENTRIES == 100000
    assert settings.RATE_LIMIT_STORAGE_TTL_SECONDS == 3600
    assert settings.RATE_LIMIT_TRUSTED_PROXY_IPS == ""
    assert settings.RATE_LIMIT_EXEMPT_PATHS == "/health,/docs,/redoc,/openapi.json"


@pytest.mark.asyncio
async def test_storage_upsert_is_atomic_under_async_concurrency() -> None:
    """Concurrent upserts should preserve a valid final state for a key."""
    storage = InMemoryRateLimitStorage(max_entries=100, ttl_seconds=3600)

    async def write_state(token_value: float) -> None:
        await storage.upsert_state(
            "client:key",
            RateLimitState(tokens=token_value, last_refill_at=1000.0 + token_value),
        )

    await asyncio.gather(*(write_state(float(value)) for value in range(1, 51)))
    state = await storage.get_state("client:key")

    assert state is not None
    assert 1.0 <= state.tokens <= 50.0


@pytest.mark.asyncio
async def test_storage_cleanup_removes_expired_entries_keeps_fresh() -> None:
    """Cleanup should prune stale entries while retaining fresh state."""
    storage = InMemoryRateLimitStorage(max_entries=10, ttl_seconds=60)

    await storage.upsert_state("stale", RateLimitState(tokens=1.0, last_refill_at=10.0))
    await storage.upsert_state("fresh", RateLimitState(tokens=1.0, last_refill_at=80.0))

    removed_count = await storage.cleanup_expired(now_monotonic=100.0)

    assert removed_count == 1
    assert await storage.get_state("stale") is None
    assert await storage.get_state("fresh") is not None


@pytest.mark.asyncio
async def test_storage_enforces_max_entries_guard() -> None:
    """Storage should evict when max entry cap is reached."""
    storage = InMemoryRateLimitStorage(max_entries=2, ttl_seconds=3600)

    await storage.upsert_state("k1", RateLimitState(tokens=1.0, last_refill_at=1.0))
    await storage.upsert_state("k2", RateLimitState(tokens=1.0, last_refill_at=2.0))
    await storage.upsert_state("k3", RateLimitState(tokens=1.0, last_refill_at=3.0))

    existing_count = sum(
        1 for key in ["k1", "k2", "k3"] if await storage.get_state(key) is not None
    )
    assert existing_count == 2
