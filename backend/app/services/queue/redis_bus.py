from __future__ import annotations

import json
import os
import time
from contextlib import suppress
from typing import Any

from app.core.config import get_settings

try:  # optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class RedisEventBus:
    """Redis Streams publisher with optional client and simple retry/backoff."""

    def __init__(self, stream: str = "events") -> None:
        self.stream = stream
        self._client = None
        url = os.getenv("REDIS_URL", get_settings().REDIS_URL)
        if redis is not None and url:
            with suppress(Exception):
                self._client = redis.Redis.from_url(url, decode_responses=True)

    def publish(self, event: dict[str, Any], max_retries: int = 3) -> str | None:
        if not self._client:
            return None
        payload = json.dumps(event)
        last_err: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return self._client.xadd(self.stream, {"data": payload})
            except Exception as err:  # noqa: BLE001
                last_err = err
                time.sleep(min(0.5 * (2**attempt), 2.0))
        raise RuntimeError(f"failed to publish after retries: {last_err}")
