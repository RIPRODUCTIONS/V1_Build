from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def app_with_auth(monkeypatch):
    monkeypatch.setenv("SECURE_MODE", "true")
    monkeypatch.setenv("INTERNAL_API_KEY", "dev-internal-key")
    return create_app()


def _headers():
    return {"X-API-Key": "dev-internal-key"}


def test_self_build_not_found_paths(app_with_auth):
    client = TestClient(app_with_auth)
    # Approve non-existent proposal
    r = client.post("/assistant/self_build/proposals/123456/approve", headers=_headers())
    assert r.status_code == 200
    assert r.json().get("status") == "not_found"

    # Apply non-existent proposal
    r = client.post("/assistant/self_build/proposals/123456/apply", headers=_headers())
    assert r.status_code == 200
    assert r.json().get("status") == "not_found"


