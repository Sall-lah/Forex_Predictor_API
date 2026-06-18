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

    # Trading subscriptions - encoded as JSON list of {"pair": str, "interval": int}
    # Parsed in @property ws_relay_subscriptions.
    TRADING_SUBSCRIPTIONS: str = "[]"

    # ML Model settings
    MODEL_DIR: str = "app/features/prediction/ml_models"
    MODEL_FILENAME: str = "lightgbm_model_forex.pkl"

    # Feature extraction settings
    PREDICTION_FETCH_CANDLES: int = 720
    MIN_ROWS_FOR_FEATURES: int = 168

    @property
    def model_path(self) -> Path:
        """Compute canonical absolute path to the ML model file."""
        base_dir = Path(__file__).resolve().parent.parent.parent
        return (base_dir / self.MODEL_DIR / self.MODEL_FILENAME).expanduser().resolve()

    @property
    def ws_relay_subscriptions(self) -> list[dict[str, int | str]]:
        """
        Parse TRADING_SUBSCRIPTIONS into a list of {pair, interval} dicts.

        Format on the wire: JSON list, e.g.
        '[{"pair": "BTC/USD", "interval": 1}]'.
        """
        import json

        raw = (self.TRADING_SUBSCRIPTIONS or "[]").strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid TRADING_SUBSCRIPTIONS JSON: {error}"
            ) from error
        if not isinstance(parsed, list):
            raise ValueError("TRADING_SUBSCRIPTIONS must be a JSON list")
        cleaned: list[dict[str, int | str]] = []
        for entry in parsed:
            if not isinstance(entry, dict):
                continue
            pair = entry.get("pair")
            interval = entry.get("interval")
            if isinstance(pair, str) and isinstance(interval, int):
                cleaned.append({"pair": pair, "interval": interval})
        return cleaned

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
