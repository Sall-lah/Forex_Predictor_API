import pytest
from app.core.exceptions import DataValidationError
from app.shared.ohlcv.pair_normalizer import display_pair, normalize_pair

def test_normalize_pair_known_pairs():
    assert normalize_pair("BTC/USD") == "XXBTZUSD"
    assert normalize_pair("BTCUSD") == "XXBTZUSD"
    assert normalize_pair("XBT/USD") == "XXBTZUSD"
    assert normalize_pair("XBTUSD") == "XXBTZUSD"
    assert normalize_pair("XXBTZUSD") == "XXBTZUSD"
    assert normalize_pair("ETH/USD") == "XETHZUSD"
    assert normalize_pair("ETHUSD") == "XETHZUSD"
    assert normalize_pair("XETHZUSD") == "XETHZUSD"

def test_normalize_pair_case_insensitive():
    assert normalize_pair("btc/usd") == "XXBTZUSD"
    assert normalize_pair(" btc/USD ") == "XXBTZUSD"
    assert normalize_pair("EthUsd") == "XETHZUSD"

def test_normalize_pair_unknown_raises():
    with pytest.raises(DataValidationError, match="Unknown or unsupported trading pair"):
        normalize_pair("INVALID")

    with pytest.raises(DataValidationError):
        normalize_pair("")


def test_display_pair_canonical_to_iso():
    """Canonical names (e.g. XXBTZUSD) must map to the ISO 4217-A3
    display form (e.g. BTC/USD) used by the Kraken v2 WebSocket API."""
    assert display_pair("XXBTZUSD") == "BTC/USD"
    assert display_pair("XETHZUSD") == "ETH/USD"


def test_display_pair_passthrough_for_display_form():
    assert display_pair("BTC/USD") == "BTC/USD"
    assert display_pair("ETH/USD") == "ETH/USD"
    assert display_pair("btc/usd") == "BTC/USD"


def test_display_pair_unknown_raises():
    with pytest.raises(DataValidationError):
        display_pair("FOO/BAR")
    with pytest.raises(DataValidationError):
        display_pair("")
