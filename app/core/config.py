"""
Application-wide configuration loaded from environment variables.

Why use pydantic-settings: Provides type-safe, validated config with
automatic .env file loading, avoiding raw os.getenv() scattered across
the codebase.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Centralized application settings.

    Values are loaded from environment variables or a `.env` file.
    The `model_config` class var tells pydantic-settings where to
    find the .env file and whether to treat variable names as
    case-insensitive.
    """

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    SECRET_KEY: str = "change-me-in-production"

    API_VERSION: str = "v1"
    API_PREFIX: str = "/api/v1"

    DATA_SOURCE_URL: str = "https://api.example.com/forex-data"

    MODEL_PATH: str = "./model/bitcoin_lstm_model.keras"
    SCALER_PATH: str = "./model/bitcoin_scaler.pkl"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings singleton.

    Why lru_cache: The settings object is immutable at runtime so we
    avoid re-reading the .env file on every call.  FastAPI's Depends()
    will invoke this once and reuse the result.
    """
    return Settings()
