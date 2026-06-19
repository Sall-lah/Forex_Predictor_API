"""
Tests for Subscriptions feature.

Verifies:
- GET /api/v1/subscriptions returns configured pairs
- Response schema matches SubscriptionResponse
- Empty config returns empty list
- ws_relay_subscriptions property returns fully typed data
"""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings


def test_subscriptions_returns_configured_pairs(client: TestClient) -> None:
    """Endpoint returns grouped subscriptions from env config."""
    mock_config = json.dumps(
        [
            {"pair": "BTC/USD", "interval": 1},
            {"pair": "BTC/USD", "interval": 5},
            {"pair": "ETH/USD", "interval": 1},
        ]
    )
    with patch(
        "app.features.subscriptions.router.settings"
    ) as mock_settings:
        mock_settings.ws_relay_subscriptions = json.loads(mock_config)
        response = client.get("/api/v1/subscriptions")

    assert response.status_code == 200
    data = response.json()
    assert "subscriptions" in data
    subs = data["subscriptions"]
    assert len(subs) == 2

    btc = next(s for s in subs if s["pair"] == "BTC/USD")
    assert sorted(btc["intervals"]) == [1, 5]

    eth = next(s for s in subs if s["pair"] == "ETH/USD")
    assert eth["intervals"] == [1]


def test_subscriptions_empty_config(client: TestClient) -> None:
    """Endpoint returns empty list when no subscriptions configured."""
    with patch(
        "app.features.subscriptions.router.settings"
    ) as mock_settings:
        mock_settings.ws_relay_subscriptions = []
        response = client.get("/api/v1/subscriptions")

    assert response.status_code == 200
    data = response.json()
    assert data["subscriptions"] == []


def test_subscriptions_schema_structure(client: TestClient) -> None:
    """Response follows SubscriptionResponse schema."""
    mock_config = json.dumps(
        [{"pair": "XRP/USD", "interval": 60}]
    )
    with patch(
        "app.features.subscriptions.router.settings"
    ) as mock_settings:
        mock_settings.ws_relay_subscriptions = json.loads(mock_config)
        response = client.get("/api/v1/subscriptions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["subscriptions"], list)
    assert len(data["subscriptions"]) == 1
    sub = data["subscriptions"][0]
    assert "pair" in sub
    assert "intervals" in sub
    assert isinstance(sub["pair"], str)
    assert isinstance(sub["intervals"], list)


def test_ws_relay_subscriptions_is_fully_typed(
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    """ws_relay_subscriptions returns list[dict[str, int | str]] with strict types.

    This contract test pins the property's type guarantees so that
    the router's removal of defensive str()/int() casts is safe.
    """
    test_json = '[{"pair": "BTC/USD", "interval": 1}, {"pair": "BTC/USD", "interval": 5}]'
    get_settings.cache_clear()
    try:
        settings = Settings(TRADING_SUBSCRIPTIONS=test_json)
        result = settings.ws_relay_subscriptions

        assert isinstance(result, list)
        assert len(result) == 2
        for entry in result:
            assert isinstance(entry, dict)
            assert isinstance(entry["pair"], str)
            assert isinstance(entry["interval"], int)

        # Also verify the lru_cache singleton path (what the router actually uses)
        get_settings.cache_clear()
        cached_settings = get_settings()
        cached_settings.TRADING_SUBSCRIPTIONS = test_json
        cached_result = cached_settings.ws_relay_subscriptions

        assert isinstance(cached_result, list)
        assert len(cached_result) == 2
        for entry in cached_result:
            assert isinstance(entry, dict)
            assert isinstance(entry["pair"], str)
            assert isinstance(entry["interval"], int)
    finally:
        get_settings.cache_clear()
