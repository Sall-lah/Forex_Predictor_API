from app.core.exceptions import DataValidationError

PAIR_MAP = {
    "BTC/USD": "XXBTZUSD",
    "BTCUSD": "XXBTZUSD",
    "XBT/USD": "XXBTZUSD",
    "XBTUSD": "XXBTZUSD",
    "XXBTZUSD": "XXBTZUSD",
    "ETH/USD": "XETHZUSD",
    "ETHUSD": "XETHZUSD",
    "XETHZUSD": "XETHZUSD",
}

def normalize_pair(pair: str) -> str:
    """
    Normalize a given trading pair to the Kraken canonical name.
    
    Args:
        pair: Trading pair to normalize (e.g. "BTC/USD")
        
    Returns:
        Kraken canonical name (e.g. "XXBTZUSD")
        
    Raises:
        DataValidationError: If the pair is unknown or not supported.
    """
    normalized = pair.strip().upper()
    if normalized not in PAIR_MAP:
        raise DataValidationError(f"Unknown or unsupported trading pair: {pair}")
    return PAIR_MAP[normalized]
