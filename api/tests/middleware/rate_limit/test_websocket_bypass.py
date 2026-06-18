"""WebSocket scope bypass tests for the rate-limit middleware."""

import asyncio

import pytest
from fastapi import FastAPI, WebSocket
from starlette.responses import Response
from starlette.testclient import TestClient

from app.middleware.rate_limit.middleware import RateLimitMiddleware
from app.middleware.rate_limit.service import RateLimiterService


class _FakeRequest:
    """Minimal request stand-in whose `scope` is a plain dict.

    Starlette's `Request` asserts that the scope type is 'http', but
    the middleware reads `request.scope` directly, so a duck-typed
    object is sufficient for the short-circuit branch.
    """

    def __init__(self, scope: dict, app=None) -> None:
        self.scope = scope
        self.app = app if app is not None else FastAPI()


def _build_settings():
    from app.core.config import Settings

    return Settings(
        API_PREFIX="/api/v1",
        RATE_LIMIT_DEFAULT_CAPACITY=2,
        RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND=0.01,
        RATE_LIMIT_PREDICTION_CAPACITY=1,
        RATE_LIMIT_PREDICTION_REFILL_RATE_PER_SECOND=0.01,
        RATE_LIMIT_HISTORICAL_CAPACITY=1,
        RATE_LIMIT_HISTORICAL_REFILL_RATE_PER_SECOND=0.01,
        RATE_LIMIT_STORAGE_MAX_ENTRIES=100,
        RATE_LIMIT_STORAGE_TTL_SECONDS=3600,
        RATE_LIMIT_TRUSTED_PROXY_IPS="",
        RATE_LIMIT_EXEMPT_PATHS="/health,/docs,/redoc,/openapi.json,/api/v1/ws/stream",
    )


def test_dispatch_short_circuits_on_websocket_scope(monkeypatch) -> None:
    """WebSocket scope must bypass the rate-limit service entirely."""
    evaluated: list[bool] = []

    async def fake_evaluate(self, request):  # type: ignore[no-untyped-def]
        evaluated.append(True)
        raise AssertionError("rate limiter should not be called for WS scope")

    monkeypatch.setattr(RateLimiterService, "evaluate", fake_evaluate)

    scope = {
        "type": "websocket",
        "method": "GET",
        "path": "/api/v1/ws/stream",
        "headers": [],
        "client": ("127.0.0.1", 12345),
    }
    request = _FakeRequest(scope)
    middleware = RateLimitMiddleware(app=FastAPI())

    async def call_next(_request) -> Response:
        return Response("ok")

    response = asyncio.run(middleware.dispatch(request, call_next))

    assert response.body == b"ok"
    assert evaluated == [], "rate limiter must not be invoked for WS scope"


def test_dispatch_runs_evaluator_on_http_scope(monkeypatch) -> None:
    """HTTP scope should still invoke the rate-limit service."""
    evaluated: list[bool] = []

    from app.middleware.rate_limit.schemas import RateLimitDecision
    from app.middleware.rate_limit.service import RateLimitServiceResult

    decision = RateLimitDecision(
        allowed=True,
        limit=1,
        remaining=1,
        reset_after_seconds=60,
        retry_after_seconds=None,
    )

    async def fake_evaluate(self, request):  # type: ignore[no-untyped-def]
        evaluated.append(True)
        return RateLimitServiceResult(is_exempt=False, decision=decision)

    monkeypatch.setattr(RateLimiterService, "evaluate", fake_evaluate)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/historic-data/live",
        "headers": [],
        "client": ("127.0.0.1", 12345),
    }
    request = _FakeRequest(scope)
    middleware = RateLimitMiddleware(app=FastAPI())

    async def call_next(_request) -> Response:
        return Response("ok")

    response = asyncio.run(middleware.dispatch(request, call_next))

    assert response.body == b"ok"
    assert evaluated == [True]


def test_websocket_upgrade_passes_through_starlette_testclient() -> None:
    """A websocket upgrade should succeed even when the path is not in
    `RATE_LIMIT_EXEMPT_PATHS`, proving the middleware short-circuit works."""

    settings = _build_settings()
    # The path is NOT in exempt list - this proves the WS short-circuit
    # path is taken, not the exempt path.
    settings_exempt_ws = settings.model_copy(
        update={
            "RATE_LIMIT_EXEMPT_PATHS": "/health,/docs,/redoc,/openapi.json",
        }
    )

    app = FastAPI()
    app.state.rate_limiter_service = RateLimiterService(settings=settings_exempt_ws)

    @app.websocket("/api/v1/ws/stream")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_text("hello")
        await websocket.close()

    app.add_middleware(RateLimitMiddleware)

    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws/stream") as ws:
            assert ws.receive_text() == "hello"
