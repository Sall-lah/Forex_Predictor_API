"""Rate-limit service orchestration for request policy enforcement."""

import asyncio
from dataclasses import dataclass

from starlette.requests import Request

from app.core.config import Settings, get_settings
from app.middleware.rate_limit.bucket import TokenBucket
from app.middleware.rate_limit.schemas import RateLimitDecision, RateLimitPolicy
from app.middleware.rate_limit.storage import InMemoryRateLimitStorage


@dataclass
class RateLimitServiceResult:
    """Result of rate-limit evaluation for an incoming request."""

    is_exempt: bool
    decision: RateLimitDecision | None


class RateLimiterService:
    """Coordinates policy lookup, client identification, and token consumption."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._bucket = TokenBucket()
        self._storage = InMemoryRateLimitStorage(
            max_entries=self._settings.RATE_LIMIT_STORAGE_MAX_ENTRIES,
            ttl_seconds=self._settings.RATE_LIMIT_STORAGE_TTL_SECONDS,
        )
        self._trusted_proxies = self._parse_csv_set(
            self._settings.RATE_LIMIT_TRUSTED_PROXY_IPS
        )
        self._exempt_paths = self._parse_csv_set(self._settings.RATE_LIMIT_EXEMPT_PATHS)
        self._state_lock = asyncio.Lock()

    @staticmethod
    def _parse_csv_set(raw_value: str) -> set[str]:
        """Parse comma-separated values into trimmed unique strings."""
        return {value.strip() for value in raw_value.split(",") if value.strip()}

    def _is_exempt_path(self, path: str) -> bool:
        """Return true when the request path is configured as exempt."""
        return path in self._exempt_paths

    def _resolve_client_ip(self, request: Request) -> str:
        """Resolve effective client IP with trusted-proxy anti-spoofing rules."""
        direct_ip = request.client.host if request.client else "unknown"
        if direct_ip not in self._trusted_proxies:
            return direct_ip

        forwarded_for = request.headers.get("x-forwarded-for", "")
        if not forwarded_for.strip():
            return direct_ip

        real_ip = forwarded_for.split(",", maxsplit=1)[0].strip()
        return real_ip or direct_ip

    def _resolve_policy(self, path: str) -> tuple[str, RateLimitPolicy]:
        """Map request path to endpoint-specific or default policy."""
        prediction_prefix = f"{self._settings.API_PREFIX}/prediction"
        historic_prefix = f"{self._settings.API_PREFIX}/historic-data"

        if path.startswith(prediction_prefix):
            return (
                "prediction",
                RateLimitPolicy(
                    capacity=self._settings.RATE_LIMIT_PREDICTION_CAPACITY,
                    refill_rate_per_second=self._settings.RATE_LIMIT_PREDICTION_REFILL_RATE_PER_SECOND,
                ),
            )

        if path.startswith(historic_prefix):
            return (
                "historic-data",
                RateLimitPolicy(
                    capacity=self._settings.RATE_LIMIT_HISTORICAL_CAPACITY,
                    refill_rate_per_second=self._settings.RATE_LIMIT_HISTORICAL_REFILL_RATE_PER_SECOND,
                ),
            )

        return (
            "default",
            RateLimitPolicy(
                capacity=self._settings.RATE_LIMIT_DEFAULT_CAPACITY,
                refill_rate_per_second=self._settings.RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND,
            ),
        )

    async def evaluate(self, request: Request) -> RateLimitServiceResult:
        """Evaluate request and return exempt or enforceable decision details."""
        path = request.url.path
        if self._is_exempt_path(path):
            return RateLimitServiceResult(is_exempt=True, decision=None)

        client_ip = self._resolve_client_ip(request)
        policy_key, policy = self._resolve_policy(path)
        state_key = f"{client_ip}:{policy_key}"

        async with self._state_lock:
            state = await self._storage.get_state(state_key)
            decision, new_state = self._bucket.consume(state=state, policy=policy)
            await self._storage.upsert_state(state_key, new_state)

        return RateLimitServiceResult(is_exempt=False, decision=decision)
