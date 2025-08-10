import os
import time
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings
from app.services.llm.router import _reset_router, get_llm_router


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


@router.get("/llm/ping")
async def llm_ping():
    s = Settings()
    msg = await get_llm_router().chat("Respond with: PONG")
    model = getattr(s, f"{s.LLM_PRIMARY.upper()}_MODEL", "local")
    return {"provider": s.LLM_PRIMARY, "model": model, "reply": msg[:200]}


@router.post("/llm/mode")
def set_llm_mode(mode: str, model: str | None = None):
    s = Settings(LLM_PRIMARY=mode)
    if model:
        key = f"{mode.upper()}_MODEL"
        if hasattr(s, key):
            setattr(s, key, model)
    _reset_router(s)
    return {
        "status": "ok",
        "primary": s.LLM_PRIMARY,
        "model": model or getattr(s, f"{mode.upper()}_MODEL", "unchanged"),
    }
