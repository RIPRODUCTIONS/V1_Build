import types
import sys

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _secure_env(monkeypatch):
    monkeypatch.setenv("SECURE_MODE", "false")  # health is public


def test_health_ready_db_failure(monkeypatch):
    import app.routers.health as mod

    class _BadConn:
        def __enter__(self):
            raise RuntimeError("db down")
        def __exit__(self, *a):
            return False

    class _BadEngine:
        def connect(self):
            return _BadConn()

    monkeypatch.setattr(mod, "engine", _BadEngine())
    client = TestClient(app)
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "not_ready"
    assert body["db"] == "fail"


def test_health_ready_redis_failure(monkeypatch):
    import app.routers.health as mod

    # Good DB
    class _GoodConn:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def execute(self, _):
            return 1

    class _GoodEngine:
        def connect(self):
            return _GoodConn()

    monkeypatch.setattr(mod, "engine", _GoodEngine())
    # Bad Redis
    class _BadRedis:
        def ping(self):
            raise RuntimeError("redis down")
        def close(self):
            return None
    # Patch the redis import used inside the router by overriding sys.modules
    monkeypatch.setitem(sys.modules, "redis", types.SimpleNamespace(from_url=lambda _u: _BadRedis()))

    client = TestClient(app)
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "not_ready"
    assert body["redis"] == "fail"


def test_celery_status_queue_depth_failure(monkeypatch):
    import app.routers.health as mod

    class _Celery:
        class _Control:
            def ping(self, timeout: float = 1.0):
                return []
        control = _Control()

    monkeypatch.setattr(mod, "celery_app", _Celery())
    # Make redis.llen raise
    class _RedisBadLLEN:
        def llen(self, _):
            raise RuntimeError("LLEN fail")
        def close(self):
            return None
    # Patch the redis import used inside the router by overriding sys.modules
    monkeypatch.setitem(sys.modules, "redis", types.SimpleNamespace(from_url=lambda _u: _RedisBadLLEN()))

    client = TestClient(app)
    r = client.get("/health/celery_status")
    assert r.status_code == 200
    body = r.json()
    assert "queues" in body and isinstance(body["queues"], dict)


