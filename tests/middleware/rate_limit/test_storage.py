"""Tests for rate-limit configuration and in-memory storage behavior."""

from app.core.config import Settings


def test_config_exposes_default_and_endpoint_rate_limits() -> None:
    """Settings should expose default and per-endpoint limit values."""
    settings = Settings()

    assert settings.RATE_LIMIT_DEFAULT_CAPACITY == 60
    assert settings.RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND == 1.0
    assert settings.RATE_LIMIT_PREDICTION_CAPACITY == 10
    assert settings.RATE_LIMIT_HISTORICAL_CAPACITY == 100


def test_config_exposes_storage_and_proxy_controls() -> None:
    """Settings should expose storage cleanup and trusted proxy controls."""
    settings = Settings()

    assert settings.RATE_LIMIT_STORAGE_MAX_ENTRIES == 100000
    assert settings.RATE_LIMIT_STORAGE_TTL_SECONDS == 3600
    assert settings.RATE_LIMIT_TRUSTED_PROXY_IPS == ""
    assert settings.RATE_LIMIT_EXEMPT_PATHS == "/health,/docs,/redoc,/openapi.json"
