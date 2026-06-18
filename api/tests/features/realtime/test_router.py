"""End-to-end WebSocket route tests against a real FastAPI app."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.features.realtime.connection_manager import ConnectionManager
from app.features.realtime.router import router as realtime_router
from app.features.realtime.schemas import CandleTick


def _settings(**overrides) -> Settings:
    base = dict(
        WS_BROADCAST_QUEUE_SIZE=64,
        WS_SLOW_CLIENT_OVERFLOW_THRESHOLD=10,
        WS_ALLOWED_ORIGINS="http://localhost:3000,http://testclient",
    )
    base.update(overrides)
    return Settings(**base)


def _build_app(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    """Stand up a minimal FastAPI app with a manually-wired manager."""
    # Stub out lazy startup so tests don't create real KrakenWSClient.
    async def _noop_start_kraken(_app) -> None:
        pass

    monkeypatch.setattr(
        "app.features.realtime.router.start_kraken_if_needed",
        _noop_start_kraken,
    )
    app = FastAPI()
    app.state.connection_manager = ConnectionManager(settings=settings)
    app.state.kraken_ws_client = None
    app.state.realtime_health = {
        "kraken_connected": False,
        "last_tick_at": None,
        "reconnect_count": 0,
        "subscriptions": [],
        "kraken_started": False,
    }
    app.include_router(realtime_router, prefix="/api/v1/ws")
    return app


def _make_tick(pair: str = "XXBTZUSD", interval: int = 1) -> CandleTick:
    return CandleTick(
        pair=pair,
        interval=interval,
        timestamp=datetime.now(tz=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1.0,
        is_closed=False,
    )


def test_ws_route_reachable_at_full_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The composite URL `/api/v1/ws/stream` should accept upgrades."""
    app = _build_app(_settings(), monkeypatch)
    with TestClient(app) as client:
        with client.websocket_connect(
            "/api/v1/ws/stream", headers={"origin": "http://localhost:3000"}
        ) as ws:
            ws.send_text(json.dumps({"action": "ping"}))
            ack = ws.receive_json()
            assert ack == {"type": "pong"}


def test_ws_route_rejects_disallowed_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Origins outside the allowlist must be rejected with code 1008."""
    app = _build_app(_settings(), monkeypatch)
    with TestClient(app) as client:
        with pytest.raises(Exception):
            with client.websocket_connect(
                "/api/v1/ws/stream",
                headers={"origin": "http://evil.example.com"},
            ):
                pass


def test_ws_route_broadcasts_tick_via_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    """A tick broadcast through the manager should reach the connected client."""
    app = _build_app(_settings(), monkeypatch)
    with TestClient(app) as client:
        with client.websocket_connect(
            "/api/v1/ws/stream", headers={"origin": "http://localhost:3000"}
        ) as ws:
            manager: ConnectionManager = app.state.connection_manager

            async def _broadcast_after_register() -> None:
                await asyncio.sleep(0.05)
                await manager.broadcast(_make_tick())

            asyncio.run(_broadcast_after_register())
            msg = ws.receive_json()
            assert msg["pair"] == "XXBTZUSD"
            assert msg["is_closed"] is False
