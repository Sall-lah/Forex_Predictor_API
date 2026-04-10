"""Concurrency and throughput validation tests for rate limiting.

This module focuses on correctness-first stress tests:
- Burst concurrency should never over-allow beyond policy capacity.
- High-volume synthetic traffic should keep accounting internally consistent.
"""

import asyncio
import os
import time
import tracemalloc

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


@pytest.mark.ratelimit_perf
def test_memory_smoke_rotating_clients_stays_bounded_with_cleanup() -> None:
    """Rotating-client smoke workload should remain bounded after cleanup."""
    service = RateLimiterService(settings=_build_perf_settings())
    service._bucket = TokenBucket(now_func=FixedClock(now=3000.0).now)

    async def run_workload() -> int:
        for index in range(12_000):
            request = _build_request(
                "/api/v1/prediction/predict",
                client_ip=f"192.0.2.{index % 800}",
            )
            _ = await service.evaluate(request)

        removed = await service._storage.cleanup_expired(now_monotonic=1_000_000.0)
        return removed

    tracemalloc.start()
    start_snapshot = tracemalloc.take_snapshot()
    removed = asyncio.run(run_workload())
    end_snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = end_snapshot.compare_to(start_snapshot, "lineno")
    total_alloc_diff = sum(stat.size_diff for stat in stats)

    assert removed > 0
    assert len(service._storage._states) == 0
    assert total_alloc_diff < 8_000_000


@pytest.mark.ratelimit_soak
def test_memory_soak_mode_runs_only_when_enabled() -> None:
    """Optional soak profile runs only with RATE_LIMIT_SOAK=1.

    Run explicitly:
        RATE_LIMIT_SOAK=1 pytest tests/middleware/rate_limit/test_performance.py -k "soak" -x
    """
    if os.getenv("RATE_LIMIT_SOAK") != "1":
        pytest.skip("Set RATE_LIMIT_SOAK=1 to run long-run soak validation.")

    service = RateLimiterService(settings=_build_perf_settings())
    service._bucket = TokenBucket(now_func=FixedClock(now=4000.0).now)

    async def run_soak() -> int:
        for index in range(100_000):
            request = _build_request(
                "/api/v1/prediction/predict",
                client_ip=f"198.51.100.{index % 1000}",
            )
            _ = await service.evaluate(request)

        removed = await service._storage.cleanup_expired(now_monotonic=2_000_000.0)
        return removed

    removed = asyncio.run(run_soak())

    assert removed > 0
    assert len(service._storage._states) == 0
