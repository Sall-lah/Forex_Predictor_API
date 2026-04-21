import logging
from app.core.config import get_settings
from app.shared.ohlcv.base import DataProvider
from app.shared.ohlcv.kraken_provider import KrakenProvider

logger = logging.getLogger(__name__)

def get_provider() -> DataProvider:
    """Factory to get the configured data provider."""
    settings = get_settings()
    
    provider_name = settings.DATA_PROVIDER.lower()
    
    if provider_name == "kraken":
        return KrakenProvider()
    else:
        logger.warning(f"Unknown data provider '{provider_name}'. Falling back to kraken.")
        return KrakenProvider()