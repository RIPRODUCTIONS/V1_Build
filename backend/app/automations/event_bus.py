from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from .events import EventContext

import redis.asyncio as redis

from .events import BusEvent


STREAM_KEY = os.getenv("AUTOMATION_EVENT_STREAM", "automation:events")
DLQ_KEY = os.getenv("AUTOMATION_EVENT_DLQ", "automation:events:dlq")


async def _client() -> redis.Redis:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(url)


async def publish_event(event: BusEvent) -> None:
    r = await _client()
    try:
        await r.xadd(STREAM_KEY, {"e": json.dumps(event)})
    finally:
        await r.aclose()


async def publish_calendar_created(user_id: str, payload: dict[str, Any], context: EventContext | None = None) -> None:
    evt: BusEvent = {
        "type": "calendar.event.created",
        "user_id": user_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "context": (context or {}),
    }
    await publish_event(evt)


