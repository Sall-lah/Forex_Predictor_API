"""Unit tests for the realtime ConnectionManager."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pytest

from app.core.config import Settings
from app.features.realtime.connection_manager import ConnectionManager
from app.features.realtime.schemas import CandleTick


def _settings(**overrides) -> Settings:
    base = dict(
        WS_BROADCAST_QUEUE_SIZE=4,
        WS_SLOW_CLIENT_OVERFLOW_THRESHOLD=3,
    )
    base.update(overrides)
    return Settings(**base)


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


class _FakeWebSocket:
    """Minimal WebSocket stand-in for the connection manager."""

    def __init__(self) -> None:
        self.accepted = False
        self.sent: list[Any] = []
        self.closed: tuple[int | None, str | None] | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: Any) -> None:
        self.sent.append(payload)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)


@pytest.mark.asyncio
async def test_connect_and_disconnect_basic() -> None:
    manager = ConnectionManager(settings=_settings())
    ws = _FakeWebSocket()
    await manager.connect(ws)  # type: ignore[arg-type]
    assert ws.accepted
    assert manager.client_count == 1
    await manager.disconnect(ws)  # type: ignore[arg-type]
    assert manager.client_count == 0


@pytest.mark.asyncio
async def test_broadcast_reaches_all_clients() -> None:
    manager = ConnectionManager(settings=_settings())
    clients = [_FakeWebSocket() for _ in range(5)]
    for ws in clients:
        await manager.connect(ws)  # type: ignore[arg-type]
    tick = _make_tick()
    await manager.broadcast(tick)
    # Give sender tasks a moment to drain.
    for _ in range(20):
        if all(c.sent for c in clients):
            break
        await asyncio.sleep(0.01)
    for ws in clients:
        assert len(ws.sent) == 1
        assert ws.sent[0]["pair"] == "XXBTZUSD"


@pytest.mark.asyncio
async def test_concurrent_add_remove_no_runtime_error() -> None:
    manager = ConnectionManager(settings=_settings())
    sockets = [_FakeWebSocket() for _ in range(10)]

    async def add(ws: _FakeWebSocket) -> None:
        await manager.connect(ws)  # type: ignore[arg-type]

    async def remove(ws: _FakeWebSocket) -> None:
        await manager.disconnect(ws)  # type: ignore[arg-type]

    # Interleave adds and removes; should not raise.
    await asyncio.gather(*[add(w) for w in sockets])
    await asyncio.gather(*[remove(w) for w in sockets])
    assert manager.client_count == 0


@pytest.mark.asyncio
async def test_slow_consumer_is_force_disconnected() -> None:
    """A client whose queue overflows beyond the threshold should be dropped."""
    settings = _settings(
        WS_BROADCAST_QUEUE_SIZE=1,
        WS_SLOW_CLIENT_OVERFLOW_THRESHOLD=2,
    )
    manager = ConnectionManager(settings=settings)
    slow = _FakeWebSocket()
    fast = _FakeWebSocket()
    await manager.connect(slow)  # type: ignore[arg-type]
    await manager.connect(fast)  # type: ignore[arg-type]

    # Block the slow sender task by replacing the send_json with a
    # coroutine that never resolves - this fills its queue.
    async def blocking_send(_payload: Any) -> None:
        await asyncio.sleep(60)

    slow.send_json = blocking_send  # type: ignore[assignment]

    for _ in range(5):
        await manager.broadcast(_make_tick())
        # Yield to the event loop so the fast sender task can drain its
        # queue. In production, broadcasts arrive at Kraken's rate
        # (~1/sec) which is naturally inter-spread with other tasks.
        await asyncio.sleep(0.05)
    # Let the force-disconnect task run.
    for _ in range(40):
        if slow.closed is not None:
            break
        await asyncio.sleep(0.05)

    assert slow.closed is not None
    assert manager.slow_disconnects >= 1
    assert manager.client_count == 1  # the fast client survives


@pytest.mark.asyncio
async def test_lock_is_held_for_every_mutation() -> None:
    """All mutating operations should acquire the asyncio lock."""
    manager = ConnectionManager(settings=_settings())
    ws = _FakeWebSocket()
    await manager.connect(ws)  # type: ignore[arg-type]
    await manager.broadcast(_make_tick())
    await manager.set_client_filter(ws, {("XXBTZUSD", 1)})  # type: ignore[arg-type]
    await manager.disconnect(ws)  # type: ignore[arg-type]
    # connect: 1, broadcast: 1, set_client_filter: 1, disconnect: 1
    assert manager._lock_acquire_count >= 4


@pytest.mark.asyncio
async def test_per_client_filter_blocks_other_pairs() -> None:
    manager = ConnectionManager(settings=_settings())
    ws = _FakeWebSocket()
    await manager.connect(ws)  # type: ignore[arg-type]
    await manager.set_client_filter(ws, {("XXBTZUSD", 1)})  # type: ignore[arg-type]
    await manager.broadcast(_make_tick(pair="XETHZUSD"))
    for _ in range(20):
        if ws.sent:
            break
        await asyncio.sleep(0.01)
    assert ws.sent == []

    await manager.broadcast(_make_tick(pair="XXBTZUSD", interval=1))
    for _ in range(20):
        if ws.sent:
            break
        await asyncio.sleep(0.01)
    assert len(ws.sent) == 1
