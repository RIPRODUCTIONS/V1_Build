from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypedDict


EventType = Literal[
    "calendar.event.created",
    "calendar.event.updated",
    "email.received",
    "task.created",
    "task.completed",
]


class EventContext(TypedDict, total=False):
    time_of_day: str
    location: str
    participants: list[str]


class BusEvent(TypedDict):
    type: EventType
    user_id: str
    ts: str
    payload: dict[str, Any]
    context: EventContext


