import os
import time
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._enabled = bool(os.getenv("RATE_LIMIT_ENABLED"))
        self._buckets: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable):
        if not self._enabled:
            return await call_next(request)
        now = time.time()
        key = request.client.host if request.client else "unknown"
        bucket = self._buckets.setdefault(key, [])
        window_start = now - 60.0
        while bucket and bucket[0] < window_start:
            bucket.pop(0)
        if len(bucket) >= self.requests_per_minute:
            from starlette.responses import JSONResponse

            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        bucket.append(now)
        return await call_next(request)
