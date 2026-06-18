"""
Realtime WebSocket route.

Exposes `ws://<host>/api/v1/ws/stream` for downstream clients. The
endpoint performs an Origin allowlist check (CSWSH mitigation),
registers the connection with the shared `ConnectionManager`, and
spawns a listener task that keeps the per-client filter set in
sync with subscribe / unsubscribe messages from the browser.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.config import get_settings
from app.features.realtime.connection_manager import (
    ConnectionManager,
    get_connection_manager,
)
from app.shared.ohlcv.pair_normalizer import normalize_pair

if TYPE_CHECKING:  # pragma: no cover
    pass

logger = logging.getLogger(__name__)

router = APIRouter()


def _origin_allowed(origin: str | None, allowed: list[str]) -> bool:
    """
    Return True when `origin` is in the allowlist (or the request has
    no Origin header, e.g. native clients and same-origin requests).
    """
    if not origin:
        # Non-browser clients (CLI tools, server-to-server) have no Origin.
        return True
    return origin in allowed


def _get_manager(websocket: WebSocket) -> ConnectionManager:
    return get_connection_manager(websocket.app)


@router.websocket("/stream")
async def ws_stream(websocket: WebSocket) -> None:
    """
    Main WebSocket endpoint.

    - Validates `Origin` against `WS_ALLOWED_ORIGINS`
    - Registers with `ConnectionManager`
    - Spawns a listener task that maintains the per-client filter
    - Streams `CandleTick` payloads until the client disconnects
    """
    settings = get_settings()
    origin = websocket.headers.get("origin")
    if not _origin_allowed(origin, settings.ws_allowed_origins):
        logger.warning(
            "event=ws_origin_reject origin=%s allowed=%s",
            origin,
            settings.ws_allowed_origins,
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    manager = _get_manager(websocket)
    await manager.connect(websocket)

    listener = asyncio.create_task(
        _listener_loop(websocket, manager),
        name=f"ws-listener-{id(websocket)}",
    )

    try:
        await listener
    except WebSocketDisconnect:
        pass
    except Exception as error:  # pragma: no cover - defensive
        logger.warning("event=ws_stream_error error=%s", error)
    finally:
        listener.cancel()
        try:
            await listener
        except (asyncio.CancelledError, Exception):
            pass
        await manager.disconnect(websocket)


async def _listener_loop(
    websocket: WebSocket, manager: ConnectionManager
) -> None:
    """
    Read client subscribe / unsubscribe messages and update the
    per-client filter on the manager. A blank payload clears the
    filter (= receive all ticks).
    """
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if not isinstance(payload, dict):
                continue
            action = payload.get("action")
            if action in ("subscribe", "unsubscribe"):
                pair = payload.get("pair")
                interval = payload.get("interval")
                if not isinstance(pair, str) or not isinstance(interval, int):
                    continue
                try:
                    canonical = normalize_pair(pair)
                except Exception:
                    continue
                key = (canonical, interval)
                if action == "subscribe":
                    manager.add_to_client_filter(websocket, key)
                else:
                    manager.remove_from_client_filter(websocket, key)
            elif action == "ping":
                try:
                    await websocket.send_json({"type": "pong"})
                except Exception:
                    return
    except WebSocketDisconnect:
        return
    except asyncio.CancelledError:
        raise
    except Exception as error:  # pragma: no cover - defensive
        logger.warning("event=ws_listener_error error=%s", error)
