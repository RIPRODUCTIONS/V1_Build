from __future__ import annotations

import os
import redis.asyncio as redis


def get_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def redis_client() -> redis.Redis:
    return redis.from_url(get_redis_url())


