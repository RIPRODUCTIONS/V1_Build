from __future__ import annotations

import abc
import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any


@dataclass(slots=True)
class OAuth2Credentials:
    access_token: str
    refresh_token: str | None = None
    expires_at_ts: int | None = None


class IntegrationError(Exception):
    pass


class RateLimitError(IntegrationError):
    pass


class IntegrationBase(abc.ABC):
    name: str

    @abc.abstractmethod
    async def discover(self, user_id: str) -> bool:
        """Return True if this integration is available for the user (credentials present)."""

    @abc.abstractmethod
    async def sync(self, user_id: str) -> dict[str, Any]:
        """Perform a sync; return summary metrics for Prometheus."""


class OAuth2Integration(IntegrationBase):
    @abc.abstractmethod
    async def get_credentials(self, user_id: str) -> OAuth2Credentials | None:
        ...

    @abc.abstractmethod
    async def refresh(self, creds: OAuth2Credentials) -> OAuth2Credentials:
        ...


class OAuth2StateStore:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def put_state(self, state: str, ttl_sec: int = 600) -> None:
        await self.redis.setex(f"oauth2:state:{state}", ttl_sec, "1")

    async def validate_and_consume(self, state: str) -> bool:
        key = f"oauth2:state:{state}"
        val = await self.redis.get(key)
        if not val:
            return False
        await self.redis.delete(key)
        return True


def rate_limiter(max_per_minute: int, bucket_key_fn: Callable[..., str]) -> Callable:
    tokens_per_second = max_per_minute / 60.0

    def decorator(func):
        last_called: dict[str, float] = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = bucket_key_fn(*args, **kwargs)
            now = time.monotonic()
            last = last_called.get(key, 0.0)
            min_interval = 1.0 / max(tokens_per_second, 0.1)
            wait = last + min_interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            last_called[key] = time.monotonic()
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 5, reset_timeout: int = 60):
        self.fail_threshold = fail_threshold
        self.reset_timeout = reset_timeout
        self._fail_count = 0
        self._state = "closed"
        self._opened_at = 0.0

    def record_success(self) -> None:
        self._fail_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._fail_count += 1
        if self._fail_count >= self.fail_threshold and self._state == "closed":
            self._state = "open"
            self._opened_at = time.monotonic()

    def allow(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open" and (time.monotonic() - self._opened_at) > self.reset_timeout:
            self._state = "half_open"
            return True
        return self._state == "half_open"



