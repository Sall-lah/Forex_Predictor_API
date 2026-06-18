"""
Application-wide configuration loaded from environment variables.

Provides type-safe, validated config with automatic .env file loading.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource


class Settings(BaseSettings):
    """
    Centralized application settings.

    Values are loaded from environment variables or .env file.
    Pydantic handles type conversion and validation automatically.
    """

    # Application settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"

    # API settings
    API_VERSION: str = "v1"
    API_PREFIX: str = "/api/v1"

    # Data Provider settings
    DATA_PROVIDER: str = "kraken"

    # Kraken API settings
    KRAKEN_OHLC_URL: str = "https://api.kraken.com/0/public/OHLC"
    KRAKEN_TIMEOUT: float = 15.0

    # Kraken WebSocket relay settings
    KRAKEN_WS_URL: str = "wss://ws.kraken.com/v2"
    KRAKEN_WS_RECONNECT_BACKOFF_SECONDS: str = "1,2,4,8,16,30"
    KRAKEN_WS_PING_INTERVAL: int = 20
    KRAKEN_WS_PING_TIMEOUT: int = 20

    # WebSocket broadcast / consumer settings
    WS_BROADCAST_QUEUE_SIZE: int = 64
    WS_SLOW_CLIENT_OVERFLOW_THRESHOLD: int = 10

    # Relay subscriptions - encoded as JSON list of {"pair": str, "interval": int}
    # Parsed in @property ws_relay_subscriptions.
    WS_RELAY_SUBSCRIPTIONS: str = "[]"

    # CSWSH mitigation - explicit origin allowlist for the WS endpoint
    # Comma-separated list of allowed origins.
    WS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ML Model settings
    MODEL_DIR: str = "app/features/prediction/ml_models"
    MODEL_FILENAME: str = "lightgbm_model_forex.pkl"

    # Feature extraction settings
    PREDICTION_FETCH_CANDLES: int = 720
    MIN_ROWS_FOR_FEATURES: int = 168

    # Rate limit defaults
    RATE_LIMIT_DEFAULT_CAPACITY: int = 60
    RATE_LIMIT_DEFAULT_REFILL_RATE_PER_SECOND: float = 1.0

    # Endpoint-specific rate limits
    RATE_LIMIT_PREDICTION_CAPACITY: int = 10
    RATE_LIMIT_PREDICTION_REFILL_RATE_PER_SECOND: float = 10 / 60
    RATE_LIMIT_HISTORICAL_CAPACITY: int = 100
    RATE_LIMIT_HISTORICAL_REFILL_RATE_PER_SECOND: float = 100 / 60

    # Storage safety controls
    RATE_LIMIT_STORAGE_MAX_ENTRIES: int = 100000
    RATE_LIMIT_STORAGE_TTL_SECONDS: int = 3600

    # Proxy and path controls
    RATE_LIMIT_TRUSTED_PROXY_IPS: str = ""
    RATE_LIMIT_EXEMPT_PATHS: str = (
        "/health,/docs,/redoc,/openapi.json,/api/v1/ws/stream"
    )

    @property
    def model_path(self) -> Path:
        """Compute canonical absolute path to the ML model file."""
        base_dir = Path(__file__).resolve().parent.parent.parent
        return (base_dir / self.MODEL_DIR / self.MODEL_FILENAME).expanduser().resolve()

    @property
    def ws_relay_subscriptions(self) -> list[dict[str, int | str]]:
        """
        Parse WS_RELAY_SUBSCRIPTIONS into a list of {pair, interval} dicts.

        Format on the wire: JSON list, e.g.
        '[{"pair": "BTC/USD", "interval": 1}]'.
        """
        import json

        raw = (self.WS_RELAY_SUBSCRIPTIONS or "[]").strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid WS_RELAY_SUBSCRIPTIONS JSON: {error}"
            ) from error
        if not isinstance(parsed, list):
            raise ValueError("WS_RELAY_SUBSCRIPTIONS must be a JSON list")
        cleaned: list[dict[str, int | str]] = []
        for entry in parsed:
            if not isinstance(entry, dict):
                continue
            pair = entry.get("pair")
            interval = entry.get("interval")
            if isinstance(pair, str) and isinstance(interval, int):
                cleaned.append({"pair": pair, "interval": interval})
        return cleaned

    @property
    def ws_allowed_origins(self) -> list[str]:
        """Parse WS_ALLOWED_ORIGINS (comma-separated) into a list."""
        return [
            origin.strip()
            for origin in (self.WS_ALLOWED_ORIGINS or "").split(",")
            if origin.strip()
        ]

    @property
    def kraken_ws_backoff_schedule(self) -> list[float]:
        """Parse KRAKEN_WS_RECONNECT_BACKOFF_SECONDS (comma-separated) into floats."""
        return [
            float(value)
            for value in (self.KRAKEN_WS_RECONNECT_BACKOFF_SECONDS or "").split(",")
            if value.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Change loading order so config from .env overrides system env variables
        return init_settings, dotenv_settings, env_settings, file_secret_settings


@lru_cache
def get_settings() -> Settings:
    """
    Return cached Settings singleton.

    Settings are loaded once and reused across the application.
    """
    return Settings()
