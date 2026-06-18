"""
Kraken v2 WebSocket client for the realtime relay.

The relay maintains a single upstream connection to
`wss://ws.kraken.com/v2`, subscribes to configured (pair, interval)
tuples, and forwards parsed ticks to a caller-supplied callback
(typically the `ConnectionManager.broadcast` sink).

Responsibilities
----------------
- Reconnect with exponential backoff (1, 2, 4, 8, 16, 30s + jitter)
- Re-subscribe every active channel after a reconnect
- Translate Kraken v2 messages into the canonical `CandleTick` shape
- Expose observability state (reconnect count, last tick, etc.)

Process-topology constraint
---------------------------
The relay must run in a single uvicorn worker. Multi-worker support
is intentionally deferred (see design.md §"Process Topology").
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Iterable

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosed

from app.core.config import Settings
from app.features.realtime.schemas import CandleTick
from app.shared.ohlcv.pair_normalizer import display_pair, normalize_pair

logger = logging.getLogger(__name__)

# Callback type the route/broadcast layer registers to receive ticks.
OnTickCallback = Callable[[CandleTick], Awaitable[None]]


class KrakenWSClient:
    """
    Long-lived background task that bridges Kraken v2 -> CandleTick.

    The client is intentionally transport-focused. It does not own the
    broadcast queue (that lives in `ConnectionManager`); it only emits
    ticks via the registered callback.

    Pair form conventions
    ---------------------
    Internally we track (canonical, interval) tuples where canonical
    is the Kraken REST form (e.g. `XXBTZUSD`). The Kraken v2 WS API
    expects the ISO 4217-A3 display form (e.g. `BTC/USD`), so the
    subscribe payload uses `display_pair()`. The inbound OHLC entries
    arrive in display form, which is what `CandleTick.pair` exposes to
    the frontend (matching the design contract).
    """

    def __init__(
        self,
        settings: Settings,
        subscriptions: Iterable[dict[str, int | str]] | None = None,
        on_tick: OnTickCallback | None = None,
    ) -> None:
        self._settings = settings
        self._subscriptions: set[tuple[str, int]] = set()
        for entry in subscriptions or []:
            pair = str(entry.get("pair", ""))
            interval = int(entry.get("interval", 0))  # type: ignore[arg-type]
            if pair and interval > 0:
                try:
                    self._subscriptions.add((normalize_pair(pair), interval))
                except Exception as error:  # pragma: no cover - defensive
                    logger.warning(
                        "event=kraken_skip_subscription pair=%s interval=%s reason=%s",
                        pair,
                        interval,
                        error,
                    )

        self._on_tick = on_tick
        self._ws: ClientConnection | None = None
        self._run_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._connected = False
        self._reconnect_count = 0
        self._last_tick_at: datetime | None = None
        self._last_successful_tick_at: datetime | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def reconnect_count(self) -> int:
        return self._reconnect_count

    @property
    def last_tick_at(self) -> datetime | None:
        return self._last_tick_at

    @property
    def last_successful_tick_at(self) -> datetime | None:
        return self._last_successful_tick_at

    @property
    def active_subscriptions(self) -> set[tuple[str, int]]:
        return set(self._subscriptions)

    def set_on_tick(self, callback: OnTickCallback) -> None:
        """Register or replace the tick callback. Used by the route layer."""
        self._on_tick = callback

    def add_subscription(self, pair: str, interval: int) -> None:
        """Track a new (pair, interval) for the next reconnect subscribe."""
        canonical = normalize_pair(pair)
        self._subscriptions.add((canonical, interval))

    async def start(self) -> None:
        """Launch the run loop as a background task."""
        if self._run_task is not None and not self._run_task.done():
            return
        self._stop_event.clear()
        self._run_task = asyncio.create_task(
            self._supervise(), name="kraken-ws-client"
        )

    async def stop(self) -> None:
        """Signal shutdown and wait for the run loop to exit."""
        self._stop_event.set()
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception as error:  # pragma: no cover - defensive
                logger.warning("event=kraken_close_error error=%s", error)
        if self._run_task is not None:
            try:
                await asyncio.wait_for(self._run_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._run_task.cancel()
            except Exception as error:  # pragma: no cover - defensive
                logger.warning("event=kraken_run_task_error error=%s", error)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _supervise(self) -> None:
        """Outer supervisor: reconnect with backoff forever until stop."""
        backoff_schedule = self._settings.kraken_ws_backoff_schedule or [1, 2, 4, 8, 16, 30]
        attempt = 0
        while not self._stop_event.is_set():
            try:
                await self._connect_and_run()
                # Clean exit (stop() called)
                break
            except asyncio.CancelledError:
                raise
            except Exception as error:
                self._connected = False
                self._reconnect_count += 1
                logger.warning(
                    "event=kraken_reconnect attempt=%d error=%s",
                    self._reconnect_count,
                    error,
                )
                delay = backoff_schedule[min(attempt, len(backoff_schedule) - 1)]
                delay += random.uniform(0, 0.3) * delay
                attempt += 1
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=delay
                    )
                    break
                except asyncio.TimeoutError:
                    continue

    async def _connect_and_run(self) -> None:
        """Single connection lifecycle: connect, subscribe, drain messages."""
        ping_interval = self._settings.KRAKEN_WS_PING_INTERVAL
        ping_timeout = self._settings.KRAKEN_WS_PING_TIMEOUT
        logger.info(
            "event=kraken_connect url=%s ping_interval=%d ping_timeout=%d",
            self._settings.KRAKEN_WS_URL,
            ping_interval,
            ping_timeout,
        )
        async with websockets.connect(
            self._settings.KRAKEN_WS_URL,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
        ) as ws:
            self._ws = ws
            self._connected = True
            try:
                await self._resubscribe_all(ws)
                await self._drain_messages(ws)
            finally:
                self._connected = False
                self._ws = None

    async def _resubscribe_all(self, ws: ClientConnection) -> None:
        """Re-send every active subscription after (re)connect."""
        if not self._subscriptions:
            return
        # Kraken v2 requires `interval` to be a scalar integer per subscribe
        # call, so we send one message per (pair, interval) tuple instead of
        # bundling multiple intervals into a list.
        for canonical_pair, interval in sorted(self._subscriptions):
            display = display_pair(canonical_pair)
            payload = {
                "method": "subscribe",
                "params": {
                    "channel": "ohlc",
                    "symbol": [display],
                    "interval": interval,
                },
            }
            await ws.send(json.dumps(payload))
            logger.info(
                "event=kraken_resubscribe pair=%s display=%s interval=%d",
                canonical_pair,
                display,
                interval,
            )

    async def subscribe(self, pair: str, interval: int) -> None:
        """
        Track a new subscription locally and send it upstream.

        Re-sending on every call is safe (Kraken dedupes by payload),
        so we don't need to track a "pending" state.
        """
        canonical = normalize_pair(pair)
        self._subscriptions.add((canonical, interval))
        if self._ws is None:
            return
        display = display_pair(canonical)
        payload = {
            "method": "subscribe",
            "params": {
                "channel": "ohlc",
                "symbol": [display],
                "interval": interval,
            },
        }
        try:
            await self._ws.send(json.dumps(payload))
            logger.info(
                "event=kraken_subscribe pair=%s display=%s interval=%d",
                canonical,
                display,
                interval,
            )
        except ConnectionClosed:
            # Will be re-subscribed on the next reconnect cycle.
            logger.debug("subscribe(): socket already closed, will retry on reconnect")

    async def _drain_messages(self, ws: ClientConnection) -> None:
        """Read and dispatch Kraken messages until the socket closes."""
        async for raw in ws:
            if self._stop_event.is_set():
                break
            try:
                message = json.loads(raw)
            except (TypeError, ValueError) as error:
                logger.warning("event=kraken_bad_json error=%s", error)
                continue
            await self._handle_message(message)

    async def _handle_message(self, message: dict) -> None:
        """Dispatch by Kraken v2 channel."""
        channel = message.get("channel")
        if channel == "heartbeat":
            # No-op; documented requirement.
            return
        if channel == "status":
            logger.info("event=kraken_status payload=%s", message)
            return
        if channel == "ohlc":
            await self._handle_ohlc_payload(message)
            return
        if "error" in message:
            logger.warning("event=kraken_error payload=%s", message)
            return
        # Unknown channel - log once at debug to avoid spam.
        logger.debug("event=kraken_unknown_channel channel=%s", channel)

    async def _handle_ohlc_payload(self, message: dict) -> None:
        """Translate a Kraken v2 ohlc message into one or more CandleTicks."""
        data = message.get("data") or []
        for entry in data:
            try:
                tick = self._map_ohlc_entry(entry)
            except Exception as error:
                logger.warning("event=kraken_ohlc_parse_error error=%s entry=%s", error, entry)
                continue
            if tick is None:
                continue
            self._last_tick_at = datetime.now(tz=timezone.utc)
            self._last_successful_tick_at = self._last_tick_at
            if self._on_tick is not None:
                try:
                    await self._on_tick(tick)
                except Exception as error:  # pragma: no cover - defensive
                    logger.warning(
                        "event=broadcast_drop reason=on_tick_error error=%s",
                        error,
                    )

    def _map_ohlc_entry(self, entry: dict) -> CandleTick | None:
        """Map one Kraken v2 OHLC entry to the canonical CandleTick."""
        raw_symbol = entry.get("symbol")
        interval_raw = entry.get("interval")
        ts_raw = entry.get("interval_begin")
        if not raw_symbol or interval_raw is None or not ts_raw:
            return None
        try:
            # Kraken v2 returns float epoch seconds in `interval_begin` for
            # some endpoints, ISO-8601 in others. Handle both.
            if isinstance(ts_raw, (int, float)):
                timestamp = datetime.fromtimestamp(float(ts_raw), tz=timezone.utc)
            else:
                ts_str = str(ts_raw).replace("Z", "+00:00")
                timestamp = datetime.fromisoformat(ts_str)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid timestamp {ts_raw!r}") from error
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        interval = int(interval_raw)
        is_closed = self._infer_is_closed(timestamp, interval)
        try:
            tick = CandleTick(
                pair=str(raw_symbol),
                interval=interval,
                timestamp=timestamp,
                open=float(entry["open"]),
                high=float(entry["high"]),
                low=float(entry["low"]),
                close=float(entry["close"]),
                volume=float(entry.get("volume", 0.0)),
                is_closed=is_closed,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid OHLC fields: {error}") from error
        return tick

    @staticmethod
    def _infer_is_closed(timestamp: datetime, interval_minutes: int) -> bool:
        """A candle is closed once its full interval has elapsed."""
        now = datetime.now(tz=timezone.utc)
        end = timestamp + timedelta(minutes=interval_minutes)
        return now >= end
