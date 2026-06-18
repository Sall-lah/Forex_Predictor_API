"""
FastAPI application instance and global exception handlers.

Why global handlers: They act as a safety net so that any unhandled
domain exception is translated into a well-structured JSON error
response, preventing raw 500 tracebacks from reaching the client.
"""

import logging
import os
import sys
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

# ---------------------------------------------------------------------------
# Single-worker enforcement via file lock
# ---------------------------------------------------------------------------

_DEFAULT_LOCK_PATH = "/tmp/kraken_ws.lock"


def _acquire_worker_lock() -> tuple[int | None, object | None]:
    """
    Attempt to acquire a cross-platform file lock to enforce single-worker
    deployment.

    Returns ``(pid, lock_handle)`` on success, ``(None, None)`` on failure.
    On Windows we use ``msvcrt.locking``; on Unix we use ``fcntl.flock``.
    """
    lock_path = os.environ.get("KRAKEN_WS_LOCK_FILE", _DEFAULT_LOCK_PATH)
    try:
        if sys.platform == "win32":
            import msvcrt

            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except OSError:
                os.close(fd)
                # Read conflicting PID from the lock file.
                try:
                    with open(lock_path, "r") as f:
                        existing_pid = int(f.read().strip())
                except (ValueError, OSError):
                    existing_pid = None
                return existing_pid, None
            # Write our PID into the lock file.
            os.write(fd, str(os.getpid()).encode())
            os.lseek(fd, 0, os.SEEK_SET)
            return os.getpid(), fd
        else:
            import fcntl

            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(fd)
                try:
                    with open(lock_path, "r") as f:
                        existing_pid = int(f.read().strip())
                except (ValueError, OSError):
                    existing_pid = None
                return existing_pid, None
            os.write(fd, str(os.getpid()).encode())
            os.lseek(fd, 0, os.SEEK_SET)
            return os.getpid(), fd
    except Exception:
        return None, None


def _release_worker_lock(lock_handle: object | None) -> None:
    """Release the file lock acquired by ``_acquire_worker_lock``."""
    if lock_handle is None:
        return
    lock_path = os.environ.get("KRAKEN_WS_LOCK_FILE", _DEFAULT_LOCK_PATH)
    try:
        if sys.platform == "win32":
            import msvcrt

            os.lseek(lock_handle, 0, os.SEEK_SET)  # type: ignore[arg-type]
            msvcrt.locking(lock_handle, msvcrt.LK_UNLCK, 1)  # type: ignore[arg-type]
            os.close(lock_handle)  # type: ignore[arg-type]
        else:
            import fcntl

            fcntl.flock(lock_handle, fcntl.LOCK_UN)  # type: ignore[arg-type]
            os.close(lock_handle)  # type: ignore[arg-type]
        try:
            os.unlink(lock_path)
        except OSError:
            pass
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application startup/shutdown lifecycle.

    Reserves ``app.state`` keys consumed by the realtime feature.
    The Kraken WS client is started lazily on the first WebSocket
    connection request (see ``start_kraken_if_needed``).

    Multi-worker enforcement: a file lock is acquired at startup to
    prevent duplicate Kraken WebSocket connections.  If another worker
    already holds the lock, the process logs an error and exits.
    """
    # Placeholder state. Populated by start_kraken_if_needed() on first
    # WebSocket connection.
    app.state.kraken_ws_client = None
    app.state.connection_manager = None
    app.state.realtime_health = {
        "kraken_connected": False,
        "last_tick_at": None,
        "reconnect_count": 0,
        "subscriptions": [],
        "kraken_started": False,
    }

    # Lazy imports to avoid circulars between features.realtime and
    # the realtime router, which itself imports these symbols.
    from app.features.realtime.connection_manager import ConnectionManager

    manager = ConnectionManager(settings=settings)
    app.state.connection_manager = manager

    # Single-worker enforcement via file lock.
    conflicting_pid, lock_handle = _acquire_worker_lock()
    if lock_handle is None and conflicting_pid is not None:
        logger.error(
            "Another Kraken WS worker is already running (PID=%s). "
            "Only a single worker is supported. Exiting.",
            conflicting_pid,
        )
        sys.exit(1)
    elif lock_handle is None and conflicting_pid is None:
        logger.warning(
            "Could not acquire worker lock; proceeding without lock enforcement."
        )
    else:
        logger.info("Worker lock acquired (PID=%d)", os.getpid())

    logger.info("Lifespan: realtime state wired (lazy startup)")

    try:
        yield
    finally:
        # Stop the Kraken WS client if it was started lazily.
        client = getattr(app.state, "kraken_ws_client", None)
        if client is not None:
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
        _release_worker_lock(lock_handle)
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
    - `realtime_health` (dict with kraken_started flag)
    """
    client = getattr(app.state, "kraken_ws_client", None)
    manager = getattr(app.state, "connection_manager", None)
    health = getattr(app.state, "realtime_health", None) or {}

    subscriptions = (
        health.get("subscriptions", [])
        if isinstance(health, dict)
        else []
    )

    kraken_started = bool(health.get("kraken_started", False)) if isinstance(health, dict) else False
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

    # Status mapping: unhealthy if upstream down > 30s (only after started).
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
            "last_tick_at": (
                last_tick_at.isoformat() if last_tick_at else None
            ),
            "reconnect_count": reconnect_count,
            "subscriptions": subscriptions,
        },
        "clients": client_stats,
    }
