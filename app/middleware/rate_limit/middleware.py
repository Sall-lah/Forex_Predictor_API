"""HTTP middleware that enforces per-request rate limits."""

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.rate_limit.service import RateLimiterService


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies rate-limit checks and emits contract-compliant headers."""

    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._default_service = RateLimiterService()

    def _resolve_service(self, request: Request) -> RateLimiterService:
        """Use app-injected service when provided, else fallback default."""
        state_service = getattr(request.app.state, "rate_limiter_service", None)
        if isinstance(state_service, RateLimiterService):
            return state_service
        return self._default_service

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        """Evaluate request quota and either continue or return 429."""
        service = self._resolve_service(request)
        result = await service.evaluate(request)
        if result.is_exempt:
            return await call_next(request)

        decision = result.decision
        if decision is None:
            return await call_next(request)

        if not decision.allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Retry after the provided interval.",
                    "retry_after_seconds": decision.retry_after_seconds,
                },
                headers={
                    "X-RateLimit-Limit": str(decision.limit),
                    "X-RateLimit-Remaining": str(decision.remaining),
                    "X-RateLimit-Reset": str(decision.reset_after_seconds),
                    "Retry-After": str(decision.retry_after_seconds or 0),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(decision.limit)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        response.headers["X-RateLimit-Reset"] = str(decision.reset_after_seconds)
        return response
