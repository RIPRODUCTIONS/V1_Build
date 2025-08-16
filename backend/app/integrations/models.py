from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class NormalizedEventData(BaseModel):
    title: str | None = None
    description: str | None = None
    participants: list[str] = []
    location: str | None = None
    monetary_value: Decimal | None = None
    tags: list[str] = []
    urgency: str | None = None


class UnifiedEvent(BaseModel):
    source: str
    timestamp: datetime
    user_id: str
    event_type: str
    raw_data: dict
    normalized_data: NormalizedEventData


