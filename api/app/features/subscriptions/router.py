"""
API routes for Subscriptions feature.

Endpoints:
- GET /subscriptions: Return configured trading pair subscriptions
"""

from fastapi import APIRouter

from app.core.config import get_settings
from app.features.subscriptions.schemas import (
    SubscriptionPair,
    SubscriptionResponse,
)

router = APIRouter()
settings = get_settings()


@router.get(
    "/subscriptions",
    response_model=SubscriptionResponse,
    summary="Get configured trading pair subscriptions",
    description=(
        "Returns the list of trading pairs and OHLC intervals configured "
        "via environment variables. The frontend uses this to know which "
        "Kraken WebSocket channels to subscribe to directly."
    ),
)
async def get_subscriptions() -> SubscriptionResponse:
    """
    Return configured trading pair subscriptions.

    Parses the TRADING_SUBSCRIPTIONS (or WS_RELAY_SUBSCRIPTIONS) env var
    and groups intervals by pair.
    """
    raw = settings.ws_relay_subscriptions

    # Group by pair
    pairs_map: dict[str, list[int]] = {}
    for entry in raw:
        pair = str(entry["pair"])
        interval = int(entry["interval"])
        pairs_map.setdefault(pair, []).append(interval)

    subscriptions = [
        SubscriptionPair(pair=pair, intervals=sorted(intervals))
        for pair, intervals in sorted(pairs_map.items())
    ]

    return SubscriptionResponse(subscriptions=subscriptions)
