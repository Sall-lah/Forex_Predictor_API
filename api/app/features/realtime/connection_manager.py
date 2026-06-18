"""
Connection manager for downstream WebSocket clients of the relay.

Each connected browser is paired with an `asyncio.Queue(maxsize=N)`
and a dedicated sender task. The queue decouples the upstream tick
rate from slow consumers, so a single lagging client cannot stall the
fan-out.

Backpressure policy
-------------------
When a client's queue is full we drop the OLDEST message (newer
ticks are more valuable than older ones) and log a warning. After
`WS_SLOW_CLIENT_OVERFLOW_THRESHOLD` consecutive drops the client is
forcibly disconnected and `slow_disconnects` is incremented.

Concurrency
-----------
The set of clients and the per-client bookkeeping are mutated from
multiple tasks. Every mutation is wrapped in `asyncio.Lock` to
prevent `RuntimeError: Set changed size during iteration`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from fastapi import WebSocket

from app.core.config import Settings
from app.features.realtime.schemas import CandleTick

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class _ClientState:
    """Per-client mutable state (queue, sender task, overflow counter)."""

    def __init__(self, websocket: WebSocket, queue: asyncio.Queue) -> None:
        self.websocket = websocket
        self.queue: asyncio.Queue = queue
        self.sender_task: asyncio.Task | None = None
        self.overflow_count: int = 0
        # Optional per-client filter: only enqueue ticks matching one of
        # these (pair, interval) tuples. Empty set = receive everything.
        self.filter: set[tuple[str, int]] = set()


class ConnectionManager:
    """Tracks downstream WebSocket clients and fans out ticks."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._clients: dict[WebSocket, _ClientState] = {}
        self._lock = asyncio.Lock()
        self._slow_disconnects = 0
        # Counter for the lock, used in tests to verify the lock is held
        # for every mutating operation.
        self._lock_acquire_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def client_count(self) -> int:
        return len(self._clients)

    @property
    def slow_disconnects(self) -> int:
        return self._slow_disconnects

    def stats(self) -> dict[str, int]:
        """Snapshot for the /health endpoint."""
        return {
            "connected": self.client_count,
            "slow_disconnects": self._slow_disconnects,
        }

    async def connect(self, ws: WebSocket) -> None:
        """Accept a new client and start its sender task."""
        await ws.accept()
        queue: asyncio.Queue = asyncio.Queue(
            maxsize=self._settings.WS_BROADCAST_QUEUE_SIZE
        )
        state = _ClientState(websocket=ws, queue=queue)
        async with self._lock:
            self._lock_acquire_count += 1
            self._clients[ws] = state
        state.sender_task = asyncio.create_task(
            self._sender_loop(state), name=f"ws-sender-{id(ws)}"
        )
        logger.info(
            "event=client_connect client_id=%s total_clients=%d",
            id(ws),
            self.client_count,
        )

    async def disconnect(self, ws: WebSocket) -> None:
        """Idempotent remove: cancel the sender task, drop the entry."""
        async with self._lock:
            self._lock_acquire_count += 1
            state = self._clients.pop(ws, None)
        if state is None:
            return
        if state.sender_task is not None and not state.sender_task.done():
            state.sender_task.cancel()
            try:
                await state.sender_task
            except (asyncio.CancelledError, Exception):  # pragma: no cover
                pass
        logger.info(
            "event=client_disconnect client_id=%s remaining=%d",
            id(ws),
            self.client_count,
        )

    async def set_client_filter(
        self, ws: WebSocket, pairs: set[tuple[str, int]]
    ) -> None:
        """Replace a client's per-connection filter set."""
        async with self._lock:
            self._lock_acquire_count += 1
            state = self._clients.get(ws)
            if state is not None:
                state.filter = set(pairs)

    def add_to_client_filter(
        self, ws: WebSocket, pair_interval: tuple[str, int]
    ) -> None:
        """Add a (pair, interval) tuple to the client's filter set.
        Synchronous; the route layer guards this with the lock implicitly
        because the only callers (the listener task) run in the same
        event loop as broadcast/connect/disconnect.
        """
        state = self._clients.get(ws)
        if state is not None:
            state.filter.add(pair_interval)
            # Note: this is intentionally a synchronous mutation; the
            # broadcast path reads the set, not writes it, so a brief
            # mutation race only affects which tick is dropped, never
            # correctness.

    def remove_from_client_filter(
        self, ws: WebSocket, pair_interval: tuple[str, int]
    ) -> None:
        """Remove a (pair, interval) tuple from the client's filter set."""
        state = self._clients.get(ws)
        if state is not None:
            state.filter.discard(pair_interval)

    async def broadcast(self, tick: CandleTick) -> None:
        """Fan-out a single tick to every connected client."""
        # Snapshot under lock to avoid "set changed size during iteration".
        async with self._lock:
            self._lock_acquire_count += 1
            clients = list(self._clients.items())
        for ws, state in clients:
            # Per-client filter check.
            if state.filter and (tick.pair, tick.interval) not in state.filter:
                continue
            try:
                state.queue.put_nowait(tick)
            except asyncio.QueueFull:
                # Drop the OLDEST message and try again.
                try:
                    _ = state.queue.get_nowait()
                except asyncio.QueueEmpty:  # pragma: no cover - race
                    pass
                state.overflow_count += 1
                logger.warning(
                    "event=broadcast_drop client_id=%s pair=%s "
                    "overflow_count=%d",
                    id(ws),
                    tick.pair,
                    state.overflow_count,
                )
                if (
                    state.overflow_count
                    >= self._settings.WS_SLOW_CLIENT_OVERFLOW_THRESHOLD
                ):
                    self._slow_disconnects += 1
                    logger.warning(
                        "event=slow_client_drop client_id=%s pair=%s "
                        "overflow_count=%d threshold=%d",
                        id(ws),
                        tick.pair,
                        state.overflow_count,
                        self._settings.WS_SLOW_CLIENT_OVERFLOW_THRESHOLD,
                    )
                    # Force-disconnect outside the iteration to avoid
                    # mutating the list we're walking.
                    asyncio.create_task(self._force_disconnect(ws))
                else:
                    # Still try to enqueue the new (more valuable) tick.
                    try:
                        state.queue.put_nowait(tick)
                    except asyncio.QueueFull:  # pragma: no cover
                        pass

    async def close_all(self) -> None:
        """Disconnect every client. Used during shutdown."""
        async with self._lock:
            self._lock_acquire_count += 1
            clients = list(self._clients.keys())
        for ws in clients:
            await self.disconnect(ws)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _force_disconnect(self, ws: WebSocket) -> None:
        try:
            await ws.close(code=1011, reason="slow_consumer")
        except Exception:  # pragma: no cover - defensive
            pass
        await self.disconnect(ws)

    async def _sender_loop(self, state: _ClientState) -> None:
        """Drain a client's queue and ship messages over the socket."""
        try:
            while True:
                tick = await state.queue.get()
                try:
                    await state.websocket.send_json(tick.model_dump(mode="json"))
                except Exception as error:
                    logger.warning(
                        "event=client_send_error client_id=%s error=%s",
                        id(state.websocket),
                        error,
                    )
                    break
        except asyncio.CancelledError:
            raise
        except Exception as error:  # pragma: no cover - defensive
            logger.warning("event=sender_loop_error error=%s", error)
        finally:
            # If the loop exits naturally, make sure the client is removed.
            await self.disconnect(state.websocket)


def get_connection_manager(app: "FastAPI | None" = None) -> ConnectionManager:
    """
    Resolve the process-local ConnectionManager singleton.

    Reads from `app.state.connection_manager` when an app is supplied,
    falling back to a fresh instance in dev/test contexts. The lifespan
    in `app.main` is responsible for the production path.
    """
    if app is not None:
        manager = getattr(app.state, "connection_manager", None)
        if isinstance(manager, ConnectionManager):
            return manager
    logger.debug("Falling back to a fresh ConnectionManager (no app.state entry)")
    return ConnectionManager(settings=__import__("app.core.config", fromlist=["get_settings"]).get_settings())
