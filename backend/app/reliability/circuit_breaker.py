import os
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SimpleCircuitBreaker(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._enabled = bool(os.getenv("CIRCUIT_BREAKER_ENABLED"))

    async def dispatch(self, request: Request, call_next: Callable[..., Awaitable]):
        if not self._enabled:
            return await call_next(request)
        # Placeholder: pass-through until configured
        return await call_next(request)
