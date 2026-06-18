"""Tests for the realtime health payload."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.features.realtime.connection_manager import ConnectionManager
from app.features.realtime.health import RealtimeHealthResponse


def _make_health_endpoint(app: FastAPI) -> None:
    """Inline the health-check logic so tests use their own state."""

    UPSTREAM_DOWN_THRESHOLD = timedelta(seconds=30)

    async def health_check() -> dict[str, object]:
        client = getattr(app.state, "kraken_ws_client", None)
        manager = getattr(app.state, "connection_manager", None)
        health = getattr(app.state, "realtime_health", None) or {}

        subscriptions = (
            health.get("subscriptions", []) if isinstance(health, dict) else []
        )
        kraken_started = bool(health.get("kraken_started", False)) if isinstance(health, dict) else False
        kraken_connected = bool(getattr(client, "connected", False)) if client else False
        last_tick_at = getattr(client, "last_tick_at", None) if client else None
        reconnect_count = int(getattr(client, "reconnect_count", 0)) if client else 0
        if last_tick_at is None and isinstance(health, dict):
            last_tick_at = health.get("last_tick_at")

        client_stats = manager.stats() if manager is not None else {
            "connected": 0,
            "slow_disconnects": 0,
        }

        now = datetime.now(tz=timezone.utc)
        upstream_down = (
            kraken_started
            and not kraken_connected
            and last_tick_at is not None
            and (now - last_tick_at) > UPSTREAM_DOWN_THRESHOLD
        )
        if upstream_down:
            status = "unhealthy"
        elif not kraken_started or not kraken_connected or client_stats.get("slow_disconnects", 0) > 0:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "upstream": {
                "kraken_started": kraken_started,
                "kraken_connected": kraken_connected,
                "last_tick_at": last_tick_at.isoformat() if last_tick_at else None,
                "reconnect_count": reconnect_count,
                "subscriptions": subscriptions,
            },
            "clients": client_stats,
        }

    app.add_api_route("/health", health_check, tags=["Health"], methods=["GET"])


def test_health_response_pydantic_round_trip() -> None:
    payload = RealtimeHealthResponse(
        status="healthy",
        upstream={
            "kraken_connected": True,
            "last_tick_at": datetime.now(tz=timezone.utc),
            "reconnect_count": 0,
            "subscriptions": [{"pair": "XXBTZUSD", "interval": 1}],
        },
        clients={"connected": 3, "slow_disconnects": 0},
    )
    serialized = payload.model_dump(mode="json")
    assert serialized["status"] == "healthy"
    assert serialized["upstream"]["kraken_connected"] is True
    assert serialized["clients"]["connected"] == 3


def test_health_endpoint_returns_extended_payload() -> None:
    local = FastAPI()
    local.state.connection_manager = ConnectionManager(settings=Settings())
    local.state.kraken_ws_client = None
    local.state.realtime_health = {
        "kraken_connected": False,
        "last_tick_at": None,
        "reconnect_count": 0,
        "subscriptions": [],
        "kraken_started": False,
    }
    _make_health_endpoint(local)

    response = TestClient(local).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "upstream" in body
    assert "kraken_started" in body["upstream"]
    assert "kraken_connected" in body["upstream"]
    assert "last_tick_at" in body["upstream"]
    assert "reconnect_count" in body["upstream"]
    assert "subscriptions" in body["upstream"]
    assert "clients" in body
    assert "connected" in body["clients"]
    assert "slow_disconnects" in body["clients"]


def test_status_unhealthy_when_upstream_down_over_threshold() -> None:
    class _StubClient:
        connected = False
        last_tick_at = datetime.now(tz=timezone.utc) - timedelta(seconds=120)
        reconnect_count = 3

    local = FastAPI()
    local.state.connection_manager = ConnectionManager(settings=Settings())
    local.state.kraken_ws_client = _StubClient()
    local.state.realtime_health = {
        "subscriptions": [],
        "kraken_started": True,
    }
    _make_health_endpoint(local)

    response = TestClient(local).get("/health")
    body = response.json()
    assert body["status"] == "unhealthy"


def test_status_degraded_when_kraken_disconnected_with_recent_tick() -> None:
    class _StubClient:
        connected = False
        last_tick_at = datetime.now(tz=timezone.utc) - timedelta(seconds=2)
        reconnect_count = 0

    local = FastAPI()
    local.state.connection_manager = ConnectionManager(settings=Settings())
    local.state.kraken_ws_client = _StubClient()
    local.state.realtime_health = {
        "subscriptions": [],
        "kraken_started": True,
    }
    _make_health_endpoint(local)

    body = TestClient(local).get("/health").json()
    assert body["status"] == "degraded"


def test_status_degraded_when_kraken_not_started() -> None:
    """Health check should report 'degraded' when client not yet started."""
    local = FastAPI()
    local.state.connection_manager = ConnectionManager(settings=Settings())
    local.state.kraken_ws_client = None
    local.state.realtime_health = {
        "subscriptions": [],
        "kraken_started": False,
    }
    _make_health_endpoint(local)

    body = TestClient(local).get("/health").json()
    assert body["status"] == "degraded"
    assert body["upstream"]["kraken_started"] is False
    assert body["upstream"]["kraken_connected"] is False


def test_healthy_when_started_and_connected() -> None:
    """Health check should report 'healthy' when started and connected."""

    class _StubClient:
        connected = True
        last_tick_at = datetime.now(tz=timezone.utc)
        reconnect_count = 0

    local = FastAPI()
    local.state.connection_manager = ConnectionManager(settings=Settings())
    local.state.kraken_ws_client = _StubClient()
    local.state.realtime_health = {
        "subscriptions": [],
        "kraken_started": True,
    }
    _make_health_endpoint(local)

    body = TestClient(local).get("/health").json()
    assert body["status"] == "healthy"
    assert body["upstream"]["kraken_started"] is True
    assert body["upstream"]["kraken_connected"] is True
