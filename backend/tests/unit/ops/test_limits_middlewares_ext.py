import time
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.ops.limits import RateLimitMiddleware, RequestTimeoutMiddleware


def _mk_app_with_rate_limit(max_requests: int = 3, window_s: int = 1):
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=max_requests, window_seconds=window_s, path_prefixes=("/assistant",))

    @app.get("/assistant/ping")
    def ping():
        return {"ok": True}

    return app


def test_rate_limit_hits_then_blocks():
    app = _mk_app_with_rate_limit(max_requests=2, window_s=1)
    client = TestClient(app)
    assert client.get("/assistant/ping").status_code == 200
    assert client.get("/assistant/ping").status_code == 200
    # Third within window should be 429
    assert client.get("/assistant/ping").status_code == 429
    # Sleep to next window
    time.sleep(1.1)
    assert client.get("/assistant/ping").status_code == 200


def test_request_timeout_returns_504():
    app = FastAPI()
    app.add_middleware(RequestTimeoutMiddleware, timeout_seconds=0.05)

    import asyncio

    @app.get("/slow")
    async def slow():  # pragma: no cover - executed under timeout
        await asyncio.sleep(0.2)
        return {"ok": True}

    client = TestClient(app)
    r = client.get("/slow")
    assert r.status_code == 504


