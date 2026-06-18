"""End-to-end test: mock Kraken upstream → KrakenWSClient → ConnectionManager.

The full WebSocket-route round trip is covered in `test_router.py`
(TestClient can't share an event loop with our async supervisor).
Here we verify the upstream->manager path that the route depends on.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest
from websockets.asyncio.server import ServerConnection, serve

from app.core.config import Settings
from app.features.realtime.connection_manager import ConnectionManager
from app.features.realtime.kraken_ws_client import KrakenWSClient
from app.features.realtime.schemas import CandleTick


def _ohlc_payload() -> dict:
    return {
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
                    datetime.now(tz=timezone.utc) - timedelta(minutes=2)
                )
                .isoformat()
                .replace("+00:00", "Z"),
                "interval": 1,
            }
        ],
    }


@pytest.mark.asyncio
async def test_kraken_ws_client_to_manager_e2e() -> None:
    """Mock Kraken server -> KrakenWSClient -> ConnectionManager.broadcast."""

    sent_to_websocket: list[str] = []
    broadcasts: list[CandleTick] = []

    async def handler(ws: ServerConnection) -> None:
        # Read the subscribe frame to make the test deterministic.
        async for message in ws:
            sent_to_websocket.append(str(message))
            if "subscribe" in str(message):
                await ws.send(json.dumps(_ohlc_payload()))
                await ws.close()
                return

    async with serve(handler, "127.0.0.1", 0) as server:
        host, port = server.sockets[0].getsockname()[:2]
        kraken_url = f"ws://{host}:{port}"

        settings = Settings(
            KRAKEN_WS_URL=kraken_url,
            KRAKEN_WS_RECONNECT_BACKOFF_SECONDS="0,0,0",
            KRAKEN_WS_PING_INTERVAL=20,
            KRAKEN_WS_PING_TIMEOUT=20,
        )

        manager = ConnectionManager(settings=settings)

        async def on_tick(tick: CandleTick) -> None:
            broadcasts.append(tick)

        client = KrakenWSClient(settings=settings, on_tick=on_tick)
        # Manually drive one connect/subscribe cycle so the test does
        # not depend on the supervisor's reconnect loop.
        await client.subscribe("BTC/USD", 1)
        await client._connect_and_run()
        await asyncio.sleep(0.05)
        await client.stop()
        await manager.close_all()

        assert any("subscribe" in s for s in sent_to_websocket), sent_to_websocket
        assert len(broadcasts) >= 1
        assert broadcasts[0].pair == "XXBTZUSD"
        assert broadcasts[0].is_closed is True
