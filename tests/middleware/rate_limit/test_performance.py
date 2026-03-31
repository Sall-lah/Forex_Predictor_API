"""Concurrency and throughput validation tests for rate limiting.

This module focuses on correctness-first stress tests:
- Burst concurrency should never over-allow beyond policy capacity.
- High-volume synthetic traffic should keep accounting internally consistent.
"""

import asyncio
import time

import pytest
from starlette.requests import Request

from app.core.config import Settings
from app.middleware.rate_limit.bucket import TokenBucket
from app.middleware.rate_limit.service import RateLimiterService


class FixedClock:
    """Deterministic clock used to make burst tests stable."""

    def __init__(self, now: float = 1000.0) -> None:
        self._now = now

    def now(self) -> float:
        """Return current fixed timestamp."""
        return self._now


def _build_perf_settings() -> Settings:
    """Return low-capacity settings for deterministic stress assertions."""
    return Settings(
        API_PREFIX="/api/v1",
        RATE_LIMIT_DEFAULT_CAPACITY=100,
        RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND=0.0 + 0.0001,
        RATE_LIMIT_PREDICTION_CAPACITY=10,
        RATE_LIMIT_PREDICTION_REFILL_RATE_PER_SECOND=0.0 + 0.0001,
        RATE_LIMIT_HISTORICAL_CAPACITY=100,
        RATE_LIMIT_HISTORICAL_REFILL_RATE_PER_SECOND=1.0,
        RATE_LIMIT_STORAGE_MAX_ENTRIES=200_000,
        RATE_LIMIT_STORAGE_TTL_SECONDS=3600,
        RATE_LIMIT_TRUSTED_PROXY_IPS="",
        RATE_LIMIT_EXEMPT_PATHS="/health,/docs,/redoc,/openapi.json",
    )


def _build_request(path: str, client_ip: str) -> Request:
    """Build a minimal Starlette request scope for service evaluation."""
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "client": (client_ip, 12345),
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )


async def _run_same_client_burst(
    service: RateLimiterService, requests: int
) -> tuple[int, int]:
    """Run concurrent requests for one client and return allow/deny totals."""

    async def evaluate_once() -> bool:
        request = _build_request("/api/v1/prediction/predict", "198.51.100.10")
        result = await service.evaluate(request)
        assert result.decision is not None
        return result.decision.allowed

    decisions = await asyncio.gather(*(evaluate_once() for _ in range(requests)))
    allowed = sum(1 for decision in decisions if decision)
    denied = requests - allowed
    return allowed, denied


@pytest.mark.ratelimit_perf
def test_concurrent_suite_requires_ratelimit_perf_marker_registration(
    pytestconfig: pytest.Config,
) -> None:
    """Concurrency suite requires explicit ratelimit_perf marker registration."""
    configured_markers = pytestconfig.getini("markers")
    assert any(marker.startswith("ratelimit_perf") for marker in configured_markers), (
        "pytest.ini must register ratelimit_perf marker"
    )


@pytest.mark.ratelimit_perf
def test_concurrent_same_client_burst_never_over_allows_capacity() -> None:
    """Concurrent burst for one client must allow at most policy capacity."""
    service = RateLimiterService(settings=_build_perf_settings())
    service._bucket = TokenBucket(now_func=FixedClock().now)

    allowed, denied = asyncio.run(_run_same_client_burst(service=service, requests=200))

    assert allowed <= 10
    assert denied >= 190


@pytest.mark.ratelimit_perf
def test_throughput_batch_accounting_stays_consistent_under_load() -> None:
    """High-volume burst should preserve correctness with observable runtime."""
    service = RateLimiterService(settings=_build_perf_settings())
    service._bucket = TokenBucket(now_func=FixedClock(now=2000.0).now)

    async def run_batch(total: int) -> tuple[int, int]:
        async def evaluate(index: int) -> bool:
            request = _build_request(
                "/api/v1/prediction/predict",
                client_ip=f"203.0.113.{index % 250}",
            )
            result = await service.evaluate(request)
            assert result.decision is not None
            return result.decision.allowed

        decisions = await asyncio.gather(*(evaluate(index) for index in range(total)))
        allowed_count = sum(1 for decision in decisions if decision)
        denied_count = total - allowed_count
        return allowed_count, denied_count

    total_requests = 5_000
    started = time.perf_counter()
    allowed_count, denied_count = asyncio.run(run_batch(total=total_requests))
    elapsed = time.perf_counter() - started

    assert allowed_count + denied_count == total_requests
    assert allowed_count <= 2_500
    assert denied_count >= 2_500
    assert elapsed < 10.0
