"""
Realtime health payload models for the extended `/health` endpoint.

Mirrors the design contract in `openspec/.../design.md §"Observability"`.
"""

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class UpstreamHealth(BaseModel):
    kraken_connected: bool = False
    last_tick_at: datetime | None = None
    reconnect_count: int = 0
    subscriptions: List[dict] = Field(default_factory=list)


class ClientsHealth(BaseModel):
    connected: int = 0
    slow_disconnects: int = 0


class RealtimeHealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    upstream: UpstreamHealth = Field(default_factory=UpstreamHealth)
    clients: ClientsHealth = Field(default_factory=ClientsHealth)
