import os
import time
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.llm.router import get_llm_router


class SimpleTimingMetrics(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._enabled = bool(os.getenv("METRICS_ENABLED"))

    async def dispatch(self, request: Request, call_next: Callable[..., Awaitable]):
        if not self._enabled:
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        _ = time.perf_counter() - start  # hook to metrics backend when enabled
        return response


router = APIRouter(tags=["ops"])


@router.get("/healthz")
def healthz():
    return {"status": "ok", "ts": time.time()}


@router.get("/readyz")
def readyz():
    return {"status": "ready"}


@router.get("/llm/ready")
async def llm_ready():
    _ = get_llm_router()
    return {"status": "ready"}
