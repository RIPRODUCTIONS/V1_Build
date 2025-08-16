import os
import time
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings
from app.services.llm.router import _reset_router, get_llm_router

# Global metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration in seconds', ['method', 'endpoint'])

class SimpleTimingMetrics(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._enabled = bool(os.getenv("METRICS_ENABLED", "true"))

    async def dispatch(self, request: Request, call_next: Callable[..., Awaitable]):
        if not self._enabled:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        # Record metrics
        endpoint = request.url.path
        method = request.method
        status = response.status_code

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

        return response


class StandaloneTimingMetrics:
    """Standalone timing metrics for testing and direct use."""

    def __init__(self) -> None:
        self._enabled = True
        # Register metrics in the global registry
        self._register_metrics()

    def _register_metrics(self) -> None:
        """Register metrics in the global Prometheus registry."""
        # The metrics are already registered globally when the module is imported
        pass

    def record_request(self, method: str, endpoint: str, status: int, duration: float) -> None:
        """Record a request manually."""
        if not self._enabled:
            return

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


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


@router.post("/llm/select_best")
async def llm_select_best():
    s = Settings()
    rt = get_llm_router()
    chosen = await rt.select_best_local()
    s.LMSTUDIO_MODEL = chosen
    _reset_router(s)
    return {"status": "ok", "chosen": chosen}
