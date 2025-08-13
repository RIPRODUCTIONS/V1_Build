from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class NormalizedEventData(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    participants: List[str] = []
    location: Optional[str] = None
    monetary_value: Optional[Decimal] = None
    tags: List[str] = []
    urgency: Optional[str] = None


class UnifiedEvent(BaseModel):
    source: str
    timestamp: datetime
    user_id: str
    event_type: str
    raw_data: dict
    normalized_data: NormalizedEventData


