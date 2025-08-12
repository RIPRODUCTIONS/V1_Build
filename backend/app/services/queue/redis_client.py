from __future__ import annotations

import redis

from app.core.config import get_settings

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    """
    Lazy, non-fatal Redis client. If not reachable and ALLOW_START_WITHOUT_REDIS=True,
    returns None and lets the app run with in-memory fallbacks.
    """
    global _redis
    if _redis is not None:
        return _redis

    try:
        client = redis.Redis.from_url(get_settings().REDIS_URL, socket_connect_timeout=0.25)
        client.ping()
        _redis = client
    except Exception:
        if get_settings().ALLOW_START_WITHOUT_REDIS:
            _redis = None
        else:
            raise
    return _redis
