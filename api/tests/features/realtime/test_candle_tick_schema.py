"""Pydantic schema validation tests for the realtime CandleTick model."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.features.realtime.schemas import (
    CandleTick,
    RelayConfigResponse,
    RelaySubscription,
    StatusBroadcast,
)


def _base_tick() -> dict:
    return {
        "pair": "BTC/USD",
        "interval": 1,
        "timestamp": datetime.now(tz=timezone.utc),
        "open": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
        "volume": 1.5,
        "is_closed": False,
    }


def test_valid_tick_passes() -> None:
    tick = CandleTick(**_base_tick())
    assert tick.pair == "BTC/USD"
    assert tick.interval == 1
    assert tick.is_closed is False


def test_missing_required_field_fails() -> None:
    payload = _base_tick()
    payload.pop("open")
    with pytest.raises(ValidationError) as exc_info:
        CandleTick(**payload)
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("open",) for err in errors)


def test_invalid_negative_price_fails() -> None:
    payload = _base_tick()
    payload["open"] = -1.0
    with pytest.raises(ValidationError):
        CandleTick(**payload)


def test_invalid_zero_interval_fails() -> None:
    payload = _base_tick()
    payload["interval"] = 0
    with pytest.raises(ValidationError):
        CandleTick(**payload)


def test_invalid_volume_negative_fails() -> None:
    payload = _base_tick()
    payload["volume"] = -1.0
    with pytest.raises(ValidationError):
        CandleTick(**payload)


def test_is_closed_boolean_required() -> None:
    payload = _base_tick()
    payload["is_closed"] = 42  # not a bool and not coercible
    with pytest.raises(ValidationError):
        CandleTick(**payload)


def test_timestamp_accepts_iso_string() -> None:
    payload = _base_tick()
    payload["timestamp"] = "2026-01-01T00:00:00Z"
    tick = CandleTick(**payload)
    assert tick.timestamp.tzinfo is not None


def test_relay_subscription_validation() -> None:
    sub = RelaySubscription(pair="BTC/USD", interval=1)
    assert sub.pair == "BTC/USD"
    with pytest.raises(ValidationError):
        RelaySubscription(pair="BTC/USD", interval=0)


def test_relay_config_response_default_subscriptions() -> None:
    response = RelayConfigResponse()
    assert response.subscriptions == []


def test_status_broadcast_defaults() -> None:
    status = StatusBroadcast()
    assert status.type == "status"
    assert status.last_successful_tick_at is None
    assert status.reconnect_count == 0
    assert status.kraken_connected is False
