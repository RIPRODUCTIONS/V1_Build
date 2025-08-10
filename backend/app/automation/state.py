# ruff: noqa: I001
import json
import time
from typing import Any

import redis.asyncio as aioredis

from app.core.config import Settings
from contextlib import suppress


def _key(run_id: str) -> str:
    return f"auto:run:{run_id}"


def _recent_key() -> str:
    return "auto:runs"


def _meta_key(run_id: str) -> str:
    return f"auto:runmeta:{run_id}"


async def set_status(run_id: str, status: str, detail: dict[str, Any] | None = None) -> None:
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    payload = {"status": status, "detail": detail or {}, "ts": time.time()}
    await r.set(_key(run_id), json.dumps(payload), ex=86400)
    # Maintain recent index (sorted by last update timestamp)
    with suppress(Exception):
        await r.zadd(_recent_key(), {run_id: payload["ts"]})


async def get_status(run_id: str) -> dict[str, Any]:
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    raw = await r.get(_key(run_id))
    return json.loads(raw) if raw else {"status": "queued", "detail": {}}


async def record_run_meta(run_id: str, intent: str, payload: dict[str, Any] | None = None) -> None:
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    data = {"intent": intent, "payload": payload or {}, "ts": time.time()}
    with suppress(Exception):
        await r.set(_meta_key(run_id), json.dumps(data), ex=86400)
        await r.zadd(_recent_key(), {run_id: data["ts"]})


async def list_recent(limit: int = 20) -> list[dict[str, Any]]:
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    run_ids = await r.zrevrange(_recent_key(), 0, max(0, limit - 1))
    results: list[dict[str, Any]] = []
    for rid in run_ids:
        st_raw = await r.get(_key(rid))
        meta_raw = await r.get(_meta_key(rid))
        status_obj = json.loads(st_raw) if st_raw else {"status": "queued", "detail": {}}
        meta_obj = json.loads(meta_raw) if meta_raw else {}
        results.append({"run_id": rid, **status_obj, "meta": meta_obj})
    return results
