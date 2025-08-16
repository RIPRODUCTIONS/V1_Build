import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL")

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class TaskQueue:
    def __init__(self, name: str = "ai_tasks"):
        self.name = name
        self._fallback_q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._redis: redis.Redis | None = None

    async def connect(self):
        if REDIS_URL and redis is not None:
            try:
                self._redis = redis.from_url(REDIS_URL, decode_responses=True)
                # ping returns bool in redis-py; treat as awaitable for asyncio client
                ping_res = self._redis.ping()  # may be coroutine or bool depending on client
                if asyncio.iscoroutine(ping_res):
                    await ping_res  # type: ignore[misc]
                logger.info("Connected to Redis queue")
                return
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to in-process queue: {e}")
        logger.info("Using in-process asyncio queue")

    async def enqueue(self, item: dict[str, Any]) -> None:
        if self._redis is not None:
            payload = json.dumps(item)
            r: Any = self._redis
            await r.lpush(self.name, payload)  # type: ignore[func-returns-value]
        else:
            await self._fallback_q.put(item)

    async def dequeue(self, block_timeout: int = 1) -> dict[str, Any] | None:
        if self._redis is not None:
            try:
                r: Any = self._redis
                res = await r.brpop([self.name], timeout=block_timeout)  # type: ignore[func-returns-value,arg-type]
                if res:
                    _key, data = res  # type: ignore[misc,assignment]
                    return json.loads(data)
            except Exception:
                return None
            return None
        try:
            return await asyncio.wait_for(self._fallback_q.get(), timeout=block_timeout)
        except TimeoutError:
            return None


async def run_worker(queue: TaskQueue, handler: Callable[[dict[str, Any]], Awaitable[None]]):
    while True:
        item = await queue.dequeue(block_timeout=2)
        if not item:
            await asyncio.sleep(0.2)
            continue
        try:
            await handler(item)
        except Exception as e:
            logger.error(f"Worker error: {e}")
