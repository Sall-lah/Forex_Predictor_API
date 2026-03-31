"""Service and middleware behavior tests for rate limiting."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.config import Settings
from app.middleware.rate_limit.middleware import RateLimitMiddleware
from app.middleware.rate_limit.service import RateLimiterService


def _build_settings() -> Settings:
    """Build test settings with low quotas for deterministic assertions."""
    return Settings(
        API_PREFIX="/api/v1",
        RATE_LIMIT_DEFAULT_CAPACITY=5,
        RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND=1.0,
        RATE_LIMIT_PREDICTION_CAPACITY=2,
        RATE_LIMIT_PREDICTION_REFILL_RATE_PER_SECOND=0.01,
        RATE_LIMIT_HISTORICAL_CAPACITY=3,
        RATE_LIMIT_HISTORICAL_REFILL_RATE_PER_SECOND=0.01,
        RATE_LIMIT_STORAGE_MAX_ENTRIES=100,
        RATE_LIMIT_STORAGE_TTL_SECONDS=3600,
        RATE_LIMIT_TRUSTED_PROXY_IPS="10.0.0.1",
        RATE_LIMIT_EXEMPT_PATHS="/health,/docs,/redoc,/openapi.json",
    )


def test_service_uses_endpoint_specific_policy_limits() -> None:
    """Prediction and historical routes should receive different configured limits."""
    app = FastAPI()
    app.state.rate_limiter_service = RateLimiterService(settings=_build_settings())

    @app.get("/api/v1/prediction/predict")
    async def prediction() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/historic-data/live")
    async def historical() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(RateLimitMiddleware)
    client = TestClient(app)

    prediction_response = client.get("/api/v1/prediction/predict")
    historical_response = client.get("/api/v1/historic-data/live")

    assert prediction_response.headers["X-RateLimit-Limit"] == "2"
    assert historical_response.headers["X-RateLimit-Limit"] == "3"


def test_service_uses_forwarded_ip_only_for_trusted_proxy() -> None:
    """X-Forwarded-For should be honored only from trusted proxy IP."""
    service = RateLimiterService(settings=_build_settings())

    request_trusted = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/prediction/predict",
            "headers": [(b"x-forwarded-for", b"203.0.113.10, 10.0.0.1")],
            "client": ("10.0.0.1", 5555),
        }
    )

    request_untrusted = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/prediction/predict",
            "headers": [(b"x-forwarded-for", b"198.51.100.20")],
            "client": ("192.0.2.55", 5555),
        }
    )

    assert service._resolve_client_ip(request_trusted) == "203.0.113.10"
    assert service._resolve_client_ip(request_untrusted) == "192.0.2.55"


def test_service_resolves_client_ip_from_trusted_proxy_chain() -> None:
    """Trusted proxy chain should resolve to first untrusted hop from the right."""
    settings = _build_settings().model_copy(
        update={"RATE_LIMIT_TRUSTED_PROXY_IPS": "10.0.0.1,10.0.0.2"}
    )
    service = RateLimiterService(settings=settings)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/prediction/predict",
            "headers": [
                (
                    b"x-forwarded-for",
                    b"203.0.113.250, 198.51.100.20, 10.0.0.2",
                )
            ],
            "client": ("10.0.0.1", 5555),
        }
    )

    assert service._resolve_client_ip(request) == "198.51.100.20"


def test_service_normalizes_exempt_paths_without_allowing_traversal() -> None:
    """Exempt matching should normalize slash/query but not traversal-like variants."""
    service = RateLimiterService(settings=_build_settings())

    assert service._is_exempt_path("/health/") is True
    assert service._is_exempt_path("/health?source=probe") is True
    assert service._is_exempt_path("/health/../api/v1/prediction/predict") is False


def test_untrusted_client_cannot_bypass_limits_by_rotating_forwarded_ip() -> None:
    """Forged XFF headers from untrusted sockets should not evade per-IP limits."""
    app = FastAPI()
    app.state.rate_limiter_service = RateLimiterService(settings=_build_settings())

    @app.get("/api/v1/prediction/predict")
    async def prediction() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(RateLimitMiddleware)
    client = TestClient(app)

    first = client.get(
        "/api/v1/prediction/predict", headers={"X-Forwarded-For": "198.51.100.1"}
    )
    second = client.get(
        "/api/v1/prediction/predict", headers={"X-Forwarded-For": "198.51.100.2"}
    )
    denied = client.get(
        "/api/v1/prediction/predict", headers={"X-Forwarded-For": "198.51.100.3"}
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert denied.status_code == 429


def test_service_bypasses_exempt_paths() -> None:
    """Operational paths should bypass rate limiting."""
    app = FastAPI()
    app.state.rate_limiter_service = RateLimiterService(settings=_build_settings())

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    app.add_middleware(RateLimitMiddleware)
    client = TestClient(app)

    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers


def test_middleware_returns_429_with_headers_and_retry_body() -> None:
    """Over-limit requests should return 429 with contract headers and JSON payload."""
    app = FastAPI()
    app.state.rate_limiter_service = RateLimiterService(settings=_build_settings())

    @app.get("/api/v1/prediction/predict")
    async def prediction() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(RateLimitMiddleware)
    client = TestClient(app)

    _ = client.get("/api/v1/prediction/predict")
    _ = client.get("/api/v1/prediction/predict")
    denied = client.get("/api/v1/prediction/predict")

    assert denied.status_code == 429
    assert denied.headers["X-RateLimit-Limit"] == "2"
    assert denied.headers["X-RateLimit-Remaining"] == "0"
    assert "X-RateLimit-Reset" in denied.headers
    assert "Retry-After" in denied.headers
    body = denied.json()
    assert "retry_after_seconds" in body


def test_middleware_includes_limit_headers_on_allowed_responses() -> None:
    """Allowed requests should include the non-429 rate-limit headers."""
    app = FastAPI()
    app.state.rate_limiter_service = RateLimiterService(settings=_build_settings())

    @app.get("/api/v1/historic-data/live")
    async def historical() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(RateLimitMiddleware)
    client = TestClient(app)

    first = client.get("/api/v1/historic-data/live")
    second = client.get("/api/v1/historic-data/live")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "3"
    assert int(second.headers["X-RateLimit-Remaining"]) <= int(
        first.headers["X-RateLimit-Remaining"]
    )
