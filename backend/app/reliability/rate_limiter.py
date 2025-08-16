import os
import time
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 10000) -> None:
        super().__init__(app)
        # Use much higher limits during testing
        import sys

        # Check if we're in testing mode
        (
            os.getenv("TESTING", "false").lower() == "true" or
            os.getenv("PYTEST_CURRENT_TEST") is not None or
            "pytest" in sys.argv[0] if len(sys.argv) > 0 else False
        )

        # Don't override intentionally set low limits during testing
        self.requests_per_minute = requests_per_minute

        self._enabled = bool(os.getenv("RATE_LIMIT_ENABLED", "true"))
        self._buckets: dict[str, list[float]] = {}

    def is_allowed(self, key: str = "default") -> bool:
        """Check if a request is allowed for the given key."""
        if not self._enabled:
            return True

        now = time.time()
        bucket = self._buckets.setdefault(key, [])
        window_start = now - 60.0

        # Remove old timestamps
        while bucket and bucket[0] < window_start:
            bucket.pop(0)

        # Check if under limit
        if len(bucket) >= self.requests_per_minute:
            return False

        # Add current timestamp
        bucket.append(now)
        return True

    async def dispatch(self, request: Request, call_next: Callable):
        if not self._enabled:
            return await call_next(request)

        key = request.client.host if request.client else "unknown"

        if not self.is_allowed(key):
            from starlette.responses import JSONResponse
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        return await call_next(request)


class StandaloneRateLimiter:
    """Standalone rate limiter for testing and direct use."""

    def __init__(self, requests_per_minute: int = 120) -> None:
        self.requests_per_minute = requests_per_minute
        self._enabled = True
        self._buckets: dict[str, list[float]] = {}

    def is_allowed(self, key: str = "default") -> bool:
        """Check if a request is allowed for the given key."""
        if not self._enabled:
            return True

        now = time.time()
        bucket = self._buckets.setdefault(key, [])
        window_start = now - 60.0

        # Remove old timestamps
        while bucket and bucket[0] < window_start:
            bucket.pop(0)

        # Check if under limit
        if len(bucket) >= self.requests_per_minute:
            return False

        # Add current timestamp
        bucket.append(now)
        return True
