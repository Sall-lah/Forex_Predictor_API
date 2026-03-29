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
    MIN_ROWS_FOR_FEATURES: int = 168

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
