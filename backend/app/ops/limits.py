from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Iterable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose declared Content-Length exceeds max_bytes.

    Note: For requests without Content-Length, this middleware allows the request.
    If strict enforcement is needed for chunked uploads, implement a custom receive wrapper.
    """

    def __init__(self, app: ASGIApp, max_bytes: int = 2_000_000) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cl = request.headers.get("content-length")
        try:
            if cl is not None and int(cl) > self.max_bytes:
                return JSONResponse({"detail": "request entity too large"}, status_code=413)
        except Exception:
            # If header is malformed, reject as bad request
            return JSONResponse({"detail": "invalid content-length"}, status_code=400)
        return await call_next(request)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Enforce a max timeout for request processing."""

    def __init__(self, app: ASGIApp, timeout_seconds: float = 15.0) -> None:
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            return JSONResponse({"detail": "request timeout"}, status_code=504)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory IP rate limiter using a sliding window.

    Not suitable for multi-process/clustered deployments; replace with Redis-based limiter in prod.
    """

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 60,
        window_seconds: int = 60,
        path_prefixes: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.path_prefixes = tuple(path_prefixes or ("/personal", "/assistant", "/investigations"))
        self._ip_to_hits: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = str(request.url.path)
        if path.startswith(self.path_prefixes):
            now = time.monotonic()
            ip = self._ip(request)
            hits = self._ip_to_hits[ip]
            # prune
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
            hits.append(now)
        return await call_next(request)

    @staticmethod
    def _ip(request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window Redis-backed rate limiter suitable for multi-instance setups.

    Key format: rl:{window}:{ip}
    Increments a counter with expiry; rejects when above max_requests.
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_url: str,
        max_requests: int = 60,
        window_seconds: int = 60,
        path_prefixes: Iterable[str] | None = None,
        namespace: str = "rl",
    ) -> None:
        super().__init__(app)
        import redis  # local import to avoid hard dep if unused

        self.r = redis.from_url(redis_url)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.path_prefixes = tuple(path_prefixes or ("/personal", "/assistant", "/investigations"))
        self.namespace = namespace

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = str(request.url.path)
        if path.startswith(self.path_prefixes):
            now = int(time.time())
            window = now // self.window_seconds
            ip = self._ip(request)
            key = f"{self.namespace}:{window}:{ip}"
            try:
                count = self.r.incr(key)
                if count == 1:
                    self.r.expire(key, self.window_seconds)
                if count > self.max_requests:
                    return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
            except Exception:
                # On Redis error, fail open and allow request
                pass
        return await call_next(request)

    @staticmethod
    def _ip(request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


