"""
FastAPI application instance and global exception handlers.

Why global handlers: They act as a safety net so that any unhandled
domain exception is translated into a well-structured JSON error
response, preventing raw 500 tracebacks from reaching the client.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    BaseAppException,
    DataFetchError,
    DataValidationError,
    InsufficientDataError,
    ModelNotLoadedError,
)
from app.middleware.rate_limit.middleware import RateLimitMiddleware
from app.api.router import api_router

settings = get_settings()

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application startup/shutdown lifecycle.

    Reserves `app.state` keys consumed by the realtime feature and
    starts the Kraken WS client as a background task. The relay must
    run in a single uvicorn worker - see design.md §"Process Topology".
    Multi-worker support requires externalising the relay to a
    dedicated process / shared bus; that is out of scope for this
    milestone.
    """
    # Placeholder state. Populated by KrakenWSClient and ConnectionManager
    # in the realtime feature.
    app.state.kraken_ws_client = None
    app.state.connection_manager = None
    app.state.realtime_health = {
        "kraken_connected": False,
        "last_tick_at": None,
        "reconnect_count": 0,
        "subscriptions": [],
    }

    # Lazy imports to avoid circulars between features.realtime and
    # the realtime router, which itself imports these symbols.
    from app.features.realtime.connection_manager import ConnectionManager
    from app.features.realtime.kraken_ws_client import KrakenWSClient

    manager = ConnectionManager(settings=settings)
    app.state.connection_manager = manager

    client = KrakenWSClient(
        settings=settings,
        subscriptions=settings.ws_relay_subscriptions,
        on_tick=manager.broadcast,
    )
    app.state.kraken_ws_client = client
    app.state.realtime_health["subscriptions"] = [
        {"pair": pair, "interval": interval}
        for pair, interval in sorted(client.active_subscriptions)
    ]

    await client.start()
    logger.info("Lifespan: realtime state wired (subscriptions=%d)", len(client.active_subscriptions))

    try:
        yield
    finally:
        try:
            await client.stop()
        except Exception as error:  # pragma: no cover - defensive
            logger.warning("Lifespan: error stopping KrakenWSClient: %s", error)
        try:
            await manager.close_all()
        except Exception as error:  # pragma: no cover - defensive
            logger.warning(
                "Lifespan: error closing ConnectionManager: %s", error
            )
        logger.info("Lifespan: shutdown complete")


app = FastAPI(
    title="Forex Predictor API",
    description="ML-powered API for historical forex data analysis and LSTM-based predictions.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)


# ---------------------------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------------------------


@app.exception_handler(ModelNotLoadedError)
async def model_not_loaded_handler(
    _request: Request, exc: ModelNotLoadedError
) -> JSONResponse:
    """Return 503 when the ML model is unavailable."""
    logger.error("ModelNotLoadedError: %s", exc.message)
    return JSONResponse(
        status_code=503,
        content={"detail": exc.message},
    )


@app.exception_handler(DataFetchError)
async def data_fetch_handler(_request: Request, exc: DataFetchError) -> JSONResponse:
    """Return 502 when an upstream data source fails."""
    logger.error("DataFetchError: %s", exc.message)
    return JSONResponse(
        status_code=502,
        content={"detail": exc.message},
    )


@app.exception_handler(DataValidationError)
async def data_validation_handler(
    _request: Request, exc: DataValidationError
) -> JSONResponse:
    """Return 422 when domain validation fails (beyond Pydantic)."""
    logger.warning("DataValidationError: %s", exc.message)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.message},
    )


@app.exception_handler(InsufficientDataError)
async def insufficient_data_handler(
    _request: Request, exc: InsufficientDataError
) -> JSONResponse:
    """Return 422 when the payload does not contain enough rows."""
    logger.warning("InsufficientDataError: %s", exc.message)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseAppException)
async def base_app_handler(_request: Request, exc: BaseAppException) -> JSONResponse:
    """
    Catch-all for any BaseAppException subclass not handled above.

    Why last: FastAPI matches handlers top-down, so more specific
    subclasses are caught first; this acts as the final fallback.
    """
    logger.error("Unhandled BaseAppException: %s", exc.message)
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message},
    )


# ---------------------------------------------------------------------------
# Router Registration
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix=settings.API_PREFIX)


# Mark upstream as "down > 30s" → unhealthy.
UPSTREAM_DOWN_THRESHOLD = timedelta(seconds=30)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, object]:
    """
    Lightweight liveness probe with realtime relay status.

    Reads from `app.state`:
    - `kraken_ws_client` (KrakenWSClient | None)
    - `connection_manager` (ConnectionManager | None)
    """
    client = getattr(app.state, "kraken_ws_client", None)
    manager = getattr(app.state, "connection_manager", None)
    health = getattr(app.state, "realtime_health", None) or {}

    subscriptions = (
        health.get("subscriptions", [])
        if isinstance(health, dict)
        else []
    )

    kraken_connected = bool(getattr(client, "connected", False)) if client else False
    last_tick_at = (
        getattr(client, "last_tick_at", None) if client else None
    )
    reconnect_count = (
        int(getattr(client, "reconnect_count", 0)) if client else 0
    )
    if last_tick_at is None and isinstance(health, dict):
        last_tick_at = health.get("last_tick_at")

    if manager is not None:
        client_stats = manager.stats()
    else:
        client_stats = {"connected": 0, "slow_disconnects": 0}

    # Status mapping: unhealthy if upstream down > 30s.
    now = datetime.now(tz=timezone.utc)
    upstream_down = (
        not kraken_connected
        and last_tick_at is not None
        and (now - last_tick_at) > UPSTREAM_DOWN_THRESHOLD
    )
    if upstream_down:
        status = "unhealthy"
    elif not kraken_connected or client_stats.get("slow_disconnects", 0) > 0:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "upstream": {
            "kraken_connected": kraken_connected,
            "last_tick_at": (
                last_tick_at.isoformat() if last_tick_at else None
            ),
            "reconnect_count": reconnect_count,
            "subscriptions": subscriptions,
        },
        "clients": client_stats,
    }
