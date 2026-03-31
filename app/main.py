"""
FastAPI application instance and global exception handlers.

Why global handlers: They act as a safety net so that any unhandled
domain exception is translated into a well-structured JSON error
response, preventing raw 500 tracebacks from reaching the client.
"""

import logging

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

app = FastAPI(
    title="Forex Predictor API",
    description="ML-powered API for historical forex data analysis and LSTM-based predictions.",
    version="0.1.0",
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


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Lightweight liveness probe for container orchestrators."""
    return {"status": "healthy"}
