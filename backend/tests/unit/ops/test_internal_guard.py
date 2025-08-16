import os

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.ops.internal_guard import InternalTokenGuard


def _make_app():
    app = FastAPI()
    app.add_middleware(InternalTokenGuard, path_prefixes=("/ops",))

    @app.get("/ops/ping")
    def ping():  # pragma: no cover - simple endpoint
        return {"ok": True}

    @app.get("/public")
    def public():
        return {"ok": True}

    return app


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("SECURE_MODE", "true")
    monkeypatch.setenv("INTERNAL_TOKEN", "secret")


def test_internal_guard_valid_token():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/ops/ping", headers={"X-Internal-Token": "secret"})
    assert r.status_code == 200


def test_internal_guard_invalid_token():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/ops/ping", headers={"X-Internal-Token": "nope"})
    assert r.status_code == 403


def test_internal_guard_missing_token():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/ops/ping")
    assert r.status_code == 403


def test_internal_guard_public_path_unaffected():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/public")
    assert r.status_code == 200


