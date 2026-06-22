import logging
from app.core.config import get_settings
from app.shared.ohlcv.kraken_provider import KrakenProvider
from app.shared.ohlcv.kraken_repository import KrakenRepository

logger = logging.getLogger(__name__)

def get_repository() -> KrakenRepository:
    """Factory to get the configured data repository with caching."""
    settings = get_settings()
    
    provider_name = settings.DATA_PROVIDER.lower()
    
    if provider_name == "kraken":
        return KrakenRepository()
    else:
        logger.warning(f"Unknown data provider '{provider_name}'. Falling back to kraken.")
        return KrakenRepository()
