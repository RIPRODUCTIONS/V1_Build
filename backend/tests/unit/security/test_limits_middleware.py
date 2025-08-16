import asyncio
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ops.limits import (
    BodySizeLimitMiddleware,
    RateLimitMiddleware,
    RedisRateLimitMiddleware,
    RequestTimeoutMiddleware,
)


def _build_app(with_middlewares: list[tuple[str, Dict[str, Any]]]) -> TestClient:
    app = FastAPI()

    @app.get("/t/ping")
    async def ping() -> Dict[str, str]:
        return {"ok": "true"}

    @app.post("/t/echo")
    async def echo(body: Dict[str, Any]) -> Dict[str, Any]:
        return body

    @app.get("/t/slow")
    async def slow() -> Dict[str, str]:
        await asyncio.sleep(0.2)
        return {"ok": "true"}

    # Install requested middlewares
    for name, kwargs in with_middlewares:
        if name == "body":
            app.add_middleware(BodySizeLimitMiddleware, **kwargs)
        elif name == "timeout":
            app.add_middleware(RequestTimeoutMiddleware, **kwargs)
        elif name == "rate":
            app.add_middleware(RateLimitMiddleware, **kwargs)
        elif name == "redis_rate":
            app.add_middleware(RedisRateLimitMiddleware, **kwargs)

    return TestClient(app)


def test_body_size_limit_rejects_large_request() -> None:
    client = _build_app([
        ("body", {"max_bytes": 10}),
    ])
    # Payload length will exceed 10 bytes
    resp = client.post("/t/echo", json={"data": "x" * 50})
    assert resp.status_code == 413
    assert "too large" in resp.json()["detail"]


def test_body_size_limit_malformed_content_length() -> None:
    client = _build_app([
        ("body", {"max_bytes": 10}),
    ])
    headers = {"content-length": "not-a-number"}
    resp = client.post("/t/echo", json={"a": 1}, headers=headers)
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"]


def test_request_timeout_returns_504() -> None:
    client = _build_app([
        ("timeout", {"timeout_seconds": 0.05}),
    ])
    resp = client.get("/t/slow")
    assert resp.status_code == 504
    assert resp.json()["detail"] == "request timeout"


def test_rate_limit_in_memory_basic() -> None:
    client = _build_app([
        ("rate", {"max_requests": 2, "window_seconds": 60, "path_prefixes": ["/t"]}),
    ])
    # Two allowed
    assert client.get("/t/ping").status_code == 200
    assert client.get("/t/ping").status_code == 200
    # Third should be limited
    resp = client.get("/t/ping")
    assert resp.status_code == 429
    assert "rate limit" in resp.json()["detail"]
    # Unrelated path should not be limited
    assert client.get("/other").status_code in (404, 405)


class _FakeRedis:
    def __init__(self) -> None:
        self._kv: Dict[str, int] = {}

    def incr(self, key: str) -> int:
        self._kv[key] = self._kv.get(key, 0) + 1
        return self._kv[key]

    def expire(self, key: str, ttl: int) -> None:  # noqa: ARG002
        return None


def test_rate_limit_redis_allows_first_blocks_second(monkeypatch) -> None:
    # Patch sys.modules['redis'] so that a local import inside middleware picks it up
    import sys, types
    fake_mod = types.SimpleNamespace(from_url=lambda _url: _FakeRedis())
    monkeypatch.setitem(sys.modules, "redis", fake_mod)

    client = _build_app([
        ("redis_rate", {"redis_url": "redis://example", "max_requests": 1, "window_seconds": 60, "path_prefixes": ["/t"]}),
    ])
    assert client.get("/t/ping").status_code == 200
    resp = client.get("/t/ping")
    assert resp.status_code == 429


def test_rate_limit_redis_fail_open_on_redis_error(monkeypatch) -> None:
    import sys, types

    class _Client:
        def incr(self, _k):
            raise RuntimeError("redis down")

        def expire(self, *_args, **_kwargs):
            return None

    fake_mod = types.SimpleNamespace(from_url=lambda _url: _Client())
    monkeypatch.setitem(sys.modules, "redis", fake_mod)

    client = _build_app([
        ("redis_rate", {"redis_url": "redis://example", "max_requests": 1, "window_seconds": 60, "path_prefixes": ["/t"]}),
    ])
    # Should not block when redis errors occur
    assert client.get("/t/ping").status_code == 200
    assert client.get("/t/ping").status_code == 200


