"""Tests for api/app/core/config.py Settings properties."""

import pytest

from app.core.config import Settings, get_settings


class TestWsRelaySubscriptions:
    """Tests for the ws_relay_subscriptions property error paths."""

    def setup_method(self) -> None:
        get_settings.cache_clear()

    def teardown_method(self) -> None:
        get_settings.cache_clear()

    def test_invalid_json_raises_value_error(self) -> None:
        """Malformed JSON string raises ValueError."""
        settings = Settings(TRADING_SUBSCRIPTIONS="not json")
        with pytest.raises(ValueError, match="Invalid TRADING_SUBSCRIPTIONS JSON"):
            settings.ws_relay_subscriptions

    def test_non_list_json_raises_value_error(self) -> None:
        """JSON that is not a list raises ValueError."""
        settings = Settings(TRADING_SUBSCRIPTIONS='{"pair": "BTC/USD"}')
        with pytest.raises(ValueError, match="TRADING_SUBSCRIPTIONS must be a JSON list"):
            settings.ws_relay_subscriptions

    def test_malformed_entries_are_skipped(self) -> None:
        """Entries with wrong types or missing fields are silently skipped."""
        raw = '[{"pair": "BTC/USD", "interval": 1}, "not-a-dict", {"pair": 42}, {"interval": 1}]'
        settings = Settings(TRADING_SUBSCRIPTIONS=raw)
        result = settings.ws_relay_subscriptions
        assert result == [{"pair": "BTC/USD", "interval": 1}]

    def test_empty_string_returns_empty_list(self) -> None:
        """Empty string returns an empty list."""
        settings = Settings(TRADING_SUBSCRIPTIONS="")
        assert settings.ws_relay_subscriptions == []
