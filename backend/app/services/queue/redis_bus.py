from __future__ import annotations

import json
import time
from typing import Any

from app.core.config import get_settings

try:  # optional dependency
    import redis  # type: ignore

    HAS_REDIS = True
except Exception:  # pragma: no cover
    HAS_REDIS = False


class RedisEventBus:
    def __init__(self, stream: str = "events") -> None:
        self.stream = stream
        self._client = None

    def _client_or_raise(self):  # pragma: no cover - trivial
        if not HAS_REDIS:
            raise RuntimeError("redis library not installed")
        if self._client is None:
            url = get_settings().REDIS_URL
            self._client = redis.Redis.from_url(url, decode_responses=True)
        return self._client

    def publish(self, event: dict[str, Any], max_retries: int = 3) -> str:
        payload = json.dumps(event)
        last_err: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                r = self._client_or_raise()
                # XADD key * field value
                msg_id = r.xadd(self.stream, {"data": payload})
                return msg_id
            except Exception as err:  # noqa: BLE001
                last_err = err
                time.sleep(min(0.5 * (2**attempt), 2.0))
        raise RuntimeError(f"failed to publish after retries: {last_err}")

from __future__ import annotations

import json
import os
from contextlib import suppress
from typing import Any

try:  # pragma: no cover - optional dependency for dev
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class RedisEventBus:
    """Lightweight Redis Streams publisher.

    If REDIS_URL is not set or redis is unavailable, publish() becomes a no-op.
    """

    def __init__(self) -> None:
        self._client = None
        url = os.getenv("REDIS_URL")
        if not url:
            return
        if redis is None:
            self._client = None
        else:
            self._client = redis.Redis.from_url(url, decode_responses=True)

    def publish(self, stream: str, event: dict[str, Any]) -> None:
        if not self._client:
            return
        data = {"data": json.dumps(event)}
        with suppress(Exception):
            self._client.xadd(stream, data)
