"""
Application-wide configuration loaded from environment variables.

Provides type-safe, validated config with automatic .env file loading.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


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

    # Kraken API settings
    KRAKEN_OHLC_URL: str = "https://api.kraken.com/0/public/OHLC"
    KRAKEN_TIMEOUT: float = 15.0
    KRAKEN_HOURLY_INTERVAL: int = 60
    KRAKEN_DEFAULT_HOURS: int = 168

    # ML Model settings
    MODEL_DIR: str = "app/features/prediction/ml_models"
    MODEL_FILENAME: str = "lightgbm_model_forex.pkl"

    # Feature extraction settings
    PREDICTION_FETCH_HOURS: int = 200
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
    RATE_LIMIT_EXEMPT_PATHS: str = "/health,/docs,/redoc,/openapi.json"

    @property
    def model_path(self) -> Path:
        """Compute full path to ML model file."""
        return Path(self.MODEL_DIR) / self.MODEL_FILENAME

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """
    Return cached Settings singleton.

    Settings are loaded once and reused across the application.
    """
    return Settings()
