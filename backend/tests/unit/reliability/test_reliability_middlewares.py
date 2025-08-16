from __future__ import annotations

from starlette.testclient import TestClient
from fastapi import FastAPI

from app.reliability.circuit_breaker import SimpleCircuitBreaker
from app.reliability.metrics import SimpleTimingMetrics
from app.reliability.rate_limiter import SlidingWindowRateLimiter


def _app_with_middlewares() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SimpleTimingMetrics)
    app.add_middleware(SimpleCircuitBreaker)
    # Middleware enables only when RATE_LIMIT_ENABLED is set; tests run with it off by default
    app.add_middleware(SlidingWindowRateLimiter, requests_per_minute=2)

    @app.get("/ok")
    async def ok():  # noqa: D401
        return {"ok": True}

    return app


def test_reliability_middlewares_rate_limit_and_ok():
    c = TestClient(_app_with_middlewares())
    assert c.get("/ok").status_code == 200
    assert c.get("/ok").status_code == 200
    # Third request: should be rate limited since we set requests_per_minute=2
    r = c.get("/ok")
    assert r.status_code == 429  # Too Many Requests


