"""Unit tests for the KrakenWSClient (mocked transport)."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest
from websockets.asyncio.server import ServerConnection, serve

from app.core.config import Settings
from app.features.realtime.kraken_ws_client import KrakenWSClient
from app.features.realtime.schemas import CandleTick


def _settings(**overrides) -> Settings:
    base = dict(
        KRAKEN_WS_URL="ws://localhost:0",  # overridden in tests
        KRAKEN_WS_RECONNECT_BACKOFF_SECONDS="0,0,0,0,0,0",
        KRAKEN_WS_PING_INTERVAL=20,
        KRAKEN_WS_PING_TIMEOUT=20,
        WS_BROADCAST_QUEUE_SIZE=64,
        WS_SLOW_CLIENT_OVERFLOW_THRESHOLD=10,
        WS_RELAY_SUBSCRIPTIONS="[]",
        WS_ALLOWED_ORIGINS="http://localhost:3000",
    )
    base.update(overrides)
    return Settings(**base)


@pytest.mark.asyncio
async def test_handle_ohlc_payload_emits_candletick(monkeypatch) -> None:
    """Feeding a v2 ohlc payload should produce a CandleTick callback."""
    captured: list[CandleTick] = []

    async def on_tick(tick: CandleTick) -> None:
        captured.append(tick)

    client = KrakenWSClient(settings=_settings(), on_tick=on_tick)

    # A 1-minute candle that started 5 minutes ago -> closed.
    closed_ts = datetime.now(tz=timezone.utc) - timedelta(minutes=5)
    payload = {
        "channel": "ohlc",
        "data": [
            {
                "symbol": "XXBTZUSD",
                "open": 100.0,
                "high": 110.0,
                "low": 95.0,
                "close": 105.0,
                "volume": 12.5,
                "interval_begin": closed_ts.isoformat().replace("+00:00", "Z"),
                "interval": 1,
            }
        ],
    }
    await client._handle_ohlc_payload(payload)

    assert len(captured) == 1
    tick = captured[0]
    assert tick.pair == "XXBTZUSD"
    assert tick.interval == 1
    assert tick.is_closed is True
    assert tick.close == 105.0


@pytest.mark.asyncio
async def test_handle_ohlc_payload_forming_candle_not_closed() -> None:
    """A fresh interval's candle should be flagged is_closed=False."""
    captured: list[CandleTick] = []

    async def on_tick(tick: CandleTick) -> None:
        captured.append(tick)

    client = KrakenWSClient(settings=_settings(), on_tick=on_tick)
    forming_ts = datetime.now(tz=timezone.utc)
    payload = {
        "channel": "ohlc",
        "data": [
            {
                "symbol": "XXBTZUSD",
                "open": 100.0,
                "high": 110.0,
                "low": 95.0,
                "close": 105.0,
                "volume": 1.0,
                "interval_begin": forming_ts.isoformat().replace("+00:00", "Z"),
                "interval": 1,
            }
        ],
    }
    await client._handle_ohlc_payload(payload)

    assert len(captured) == 1
    assert captured[0].is_closed is False


@pytest.mark.asyncio
async def test_heartbeat_does_not_invoke_callback() -> None:
    """Heartbeat messages should be dropped silently."""
    captured: list[CandleTick] = []

    async def on_tick(tick: CandleTick) -> None:
        captured.append(tick)

    client = KrakenWSClient(settings=_settings(), on_tick=on_tick)
    await client._handle_message({"channel": "heartbeat"})
    assert captured == []


@pytest.mark.asyncio
async def test_ohlc_timestamp_can_be_float_epoch() -> None:
    """Some Kraken endpoints return float epoch seconds; handle both."""
    captured: list[CandleTick] = []

    async def on_tick(tick: CandleTick) -> None:
        captured.append(tick)

    client = KrakenWSClient(settings=_settings(), on_tick=on_tick)
    payload = {
        "channel": "ohlc",
        "data": [
            {
                "symbol": "XETHZUSD",
                "open": 1.0,
                "high": 2.0,
                "low": 0.5,
                "close": 1.5,
                "volume": 5.0,
                "interval_begin": 1700000000.0,
                "interval": 60,
            }
        ],
    }
    await client._handle_ohlc_payload(payload)
    assert len(captured) == 1
    assert captured[0].pair == "XETHZUSD"
    assert captured[0].interval == 60


@pytest.mark.asyncio
async def test_ohlc_parse_error_is_swallowed() -> None:
    """Malformed entries should log a warning and not raise."""
    captured: list[CandleTick] = []

    async def on_tick(tick: CandleTick) -> None:
        captured.append(tick)

    client = KrakenWSClient(settings=_settings(), on_tick=on_tick)
    bad_payload = {
        "channel": "ohlc",
        "data": [{"symbol": "XXBTZUSD"}],  # missing required fields
    }
    await client._handle_ohlc_payload(bad_payload)
    assert captured == []


@pytest.mark.asyncio
async def test_resubscribe_all_sends_for_every_active_pair() -> None:
    """After reconnect, every tracked (pair, interval) must be re-subscribed.

    The wire payload must use the display form (`BTC/USD`) per the
    Kraken v2 API contract - not the canonical (`XXBTZUSD`) form.
    """
    client = KrakenWSClient(
        settings=_settings(),
        subscriptions=[{"pair": "BTC/USD", "interval": 1}, {"pair": "ETH/USD", "interval": 5}],
    )

    sent: list[str] = []

    class _FakeWS:
        async def send(self, data: str) -> None:
            sent.append(data)

    await client._resubscribe_all(_FakeWS())  # type: ignore[arg-type]

    decoded = [json.loads(item) for item in sent]
    symbols = {
        symbol
        for entry in decoded
        for symbol in (entry.get("params", {}).get("symbol") or [])
    }
    assert "BTC/USD" in symbols
    assert "ETH/USD" in symbols
    # Canonical form must NEVER appear on the wire.
    assert "XXBTZUSD" not in symbols
    assert "XETHZUSD" not in symbols


@pytest.mark.asyncio
async def test_full_cycle_against_local_server() -> None:
    """Integration-lite: a local websockets server feeds a v2 message
    end-to-end through the KrakenWSClient."""

    # Local server sends one ohlc update and then closes.
    async def handler(ws: ServerConnection) -> None:
        await ws.send(
            json.dumps(
                {
                    "channel": "ohlc",
                    "data": [
                        {
                            "symbol": "XXBTZUSD",
                            "open": 100.0,
                            "high": 110.0,
                            "low": 95.0,
                            "close": 105.0,
                            "volume": 1.0,
                            "interval_begin": (
                                datetime.now(tz=timezone.utc)
                                - timedelta(minutes=2)
                            ).isoformat()
                            .replace("+00:00", "Z"),
                            "interval": 1,
                        }
                    ],
                }
            )
        )
        await ws.close()

    async with serve(handler, "127.0.0.1", 0) as server:
        host, port = server.sockets[0].getsockname()[:2]
        url = f"ws://{host}:{port}"
        settings = _settings(KRAKEN_WS_URL=url)

        captured: list[CandleTick] = []

        async def on_tick(tick: CandleTick) -> None:
            captured.append(tick)

        client = KrakenWSClient(settings=settings, on_tick=on_tick)
        # We can't easily stop the supervisor's reconnect loop in a
        # short test, so we just run one cycle and stop.
        await client._connect_and_run()  # exits cleanly after the server closes
        # Allow the supervisor task to settle.
        await asyncio.sleep(0)
        assert client.connected is False
        assert len(captured) >= 1
        assert captured[0].pair == "XXBTZUSD"


# ------------------------------------------------------------------
# start_kraken_if_needed tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_kraken_if_needed_creates_client(monkeypatch) -> None:
    """start_kraken_if_needed should create and store a KrakenWSClient."""
    from fastapi import FastAPI

    from app.features.realtime.kraken_ws_client import start_kraken_if_needed

    app = FastAPI()
    app.state.kraken_ws_client = None
    app.state.connection_manager = None
    app.state.realtime_health = {
        "kraken_connected": False,
        "last_tick_at": None,
        "reconnect_count": 0,
        "subscriptions": [],
    }

    # Stub Settings to avoid env var issues
    monkeypatch.setattr(
        "app.features.realtime.kraken_ws_client.Settings",
        lambda: _settings(),
    )
    # Stub KrakenWSClient.start to avoid real WS connection
    monkeypatch.setattr(
        "app.features.realtime.kraken_ws_client.KrakenWSClient.start",
        lambda self: None,
    )

    await start_kraken_if_needed(app)

    assert app.state.kraken_ws_client is not None
    assert isinstance(app.state.kraken_ws_client, KrakenWSClient)
    assert app.state.connection_manager is not None
    assert app.state.realtime_health["kraken_started"] is True


@pytest.mark.asyncio
async def test_start_kraken_if_needed_is_noop_when_already_started(monkeypatch) -> None:
    """If client already exists, start_kraken_if_needed should be a no-op."""
    from fastapi import FastAPI

    from app.features.realtime.kraken_ws_client import start_kraken_if_needed

    existing = object()
    app = FastAPI()
    app.state.kraken_ws_client = existing

    await start_kraken_if_needed(app)

    # Should not have been replaced
    assert app.state.kraken_ws_client is existing


@pytest.mark.asyncio
async def test_start_kraken_if_needed_handles_start_failure(monkeypatch) -> None:
    """If client.start() raises, the function should log and not propagate."""
    from fastapi import FastAPI

    from app.features.realtime.kraken_ws_client import start_kraken_if_needed

    app = FastAPI()
    app.state.kraken_ws_client = None
    app.state.connection_manager = None
    app.state.realtime_health = {
        "kraken_connected": False,
        "last_tick_at": None,
        "reconnect_count": 0,
        "subscriptions": [],
    }

    monkeypatch.setattr(
        "app.features.realtime.kraken_ws_client.Settings",
        lambda: _settings(),
    )

    async def _fail_start(self):
        raise ConnectionError("network error")

    monkeypatch.setattr(
        "app.features.realtime.kraken_ws_client.KrakenWSClient.start",
        _fail_start,
    )

    # Should not raise
    await start_kraken_if_needed(app)

    # Client should still be stored (it was created, just failed to start)
    assert app.state.kraken_ws_client is not None
