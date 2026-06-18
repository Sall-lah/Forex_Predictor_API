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

# Inverse lookup for converting canonical -> display form (used by the
# Kraken v2 WebSocket API which requires ISO 4217-A3 display strings).
_CANONICAL_TO_DISPLAY: dict[str, str] = {}
for _display, _canonical in PAIR_MAP.items():
    if "/" in _display and _canonical not in _CANONICAL_TO_DISPLAY:
        _CANONICAL_TO_DISPLAY[_canonical] = _display


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


def display_pair(pair: str) -> str:
    """
    Convert any supported pair form to its ISO 4217-A3 display form
    (e.g. `BTC/USD`). Raises if the pair is unknown.

    Used for the Kraken v2 WebSocket subscribe payload, which
    requires display form (the REST API uses canonical names).
    """
    normalized = pair.strip().upper()
    if normalized not in PAIR_MAP:
        raise DataValidationError(f"Unknown or unsupported trading pair: {pair}")
    return _CANONICAL_TO_DISPLAY[PAIR_MAP[normalized]]
