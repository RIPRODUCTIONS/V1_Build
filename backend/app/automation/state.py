# ruff: noqa: I001
import json
import time
from typing import Any

import redis.asyncio as aioredis

from app.core.config import Settings


def _key(run_id: str) -> str:
    return f"auto:run:{run_id}"


async def set_status(run_id: str, status: str, detail: dict[str, Any] | None = None) -> None:
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    payload = {"status": status, "detail": detail or {}, "ts": time.time()}
    await r.set(_key(run_id), json.dumps(payload), ex=86400)


async def get_status(run_id: str) -> dict[str, Any]:
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    raw = await r.get(_key(run_id))
    return json.loads(raw) if raw else {"status": "queued", "detail": {}}
