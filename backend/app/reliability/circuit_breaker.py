import os
import time
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SimpleCircuitBreaker(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._enabled = bool(os.getenv('CIRCUIT_BREAKER_ENABLED'))

    async def dispatch(self, request: Request, call_next: Callable[..., Awaitable]):
        if not self._enabled:
            return await call_next(request)
        # Placeholder: pass-through until configured
        return await call_next(request)


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 3, reset_timeout: float = 30.0):
        self.fail_threshold = fail_threshold
        self.reset_timeout = reset_timeout
        self.fail_count = 0
        self.opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.time() - self.opened_at >= self.reset_timeout:
            # half-open
            self.fail_count = 0
            self.opened_at = None
            return False
        return True

    def record_success(self) -> None:
        self.fail_count = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.fail_count += 1
        if self.fail_count >= self.fail_threshold:
            self.opened_at = time.time()
