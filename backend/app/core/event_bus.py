from __future__ import annotations

import contextlib
import json
import os
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, cast

import redis.asyncio as redis
from app.core.config import get_settings

STREAM_KEY = os.getenv("SYSTEM_EVENT_STREAM", "system:events")
DLQ_LIST = os.getenv("SYSTEM_EVENT_DLQ", "dlq:system_events")
PROCESSED_SET = f"{STREAM_KEY}:processed"


async def _client() -> redis.Redis:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(url)


class SystemEventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = {}

    async def publish(self, event_type: str, data: dict[str, Any], source: str) -> str:
        r = await _client()
        try:
            payload = {
                "type": event_type,
                "source": source,
                "ts": datetime.now(UTC).isoformat(),
                "data": data,
            }
            # xadd returns bytes | int depending on client; coerce to str for typing
            entry_id = await r.xadd(STREAM_KEY, {"e": json.dumps(payload)})
            return str(entry_id)
        finally:
            await r.aclose()

    async def subscribe(self, event_type: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def ensure_consumer_group(self, stream: str, group: str) -> None:
        r = await _client()
        try:
            try:
                await r.xgroup_create(stream, group, id="$", mkstream=True)
            except Exception:
                # likely already exists
                pass
        finally:
            await r.aclose()

    async def consume(self, group: str, name: str, count: int = 10, block_ms: int = 2000) -> None:
        r = await _client()
        try:
            await self.ensure_consumer_group(STREAM_KEY, group)
            while True:
                resp = await r.xreadgroup(group, name, streams={STREAM_KEY: ">"}, count=count, block=block_ms)
                for _, entries in resp or []:
                    for entry_id, fields in entries:
                        try:
                            # Idempotency: skip if already processed
                            if await cast(Awaitable[Any], r.sismember(PROCESSED_SET, entry_id)):
                                await cast(Awaitable[Any], r.xack(STREAM_KEY, group, entry_id))
                                continue
                            payload = json.loads(fields.get("e", "{}"))
                            et = payload.get("type")
                            for h in self._handlers.get(et, []):
                                await h(payload)
                            await cast(Awaitable[Any], r.sadd(PROCESSED_SET, entry_id))
                            # Cap processed set size
                            try:
                                cap = get_settings().EVENT_PROCESSED_CAP
                            except Exception:
                                cap = 10000
                            # Trim by scanning and removing oldest via XREVRANGE reference if needed (best-effort)
                            try:
                                current = int(await cast(Awaitable[Any], r.scard(PROCESSED_SET)))
                                if current and current > cap:
                                    # naive trim: pop arbitrary members to keep under cap
                                    for _ in range(int(current - cap)):
                                        await cast(Awaitable[Any], r.spop(PROCESSED_SET))
                            except Exception:
                                pass
                            await cast(Awaitable[Any], r.xack(STREAM_KEY, group, entry_id))
                        except Exception:
                            # Push to DLQ with original fields and entry id
                            with contextlib.suppress(Exception):
                                await cast(
                                    Awaitable[Any],
                                    r.lpush(
                                        DLQ_LIST,
                                        json.dumps({
                                            "id": entry_id,
                                            "stream": STREAM_KEY,
                                            "group": group,
                                            "fields": {k: v for k, v in fields.items()},
                                        }),
                                    ),
                                )
                            # Leave unacked for retry
        finally:
            await r.aclose()


