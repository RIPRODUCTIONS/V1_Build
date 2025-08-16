import os

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("SECURE_MODE", "true")
    monkeypatch.setenv("INTERNAL_API_KEY", "dev-internal-key")
    # Force sync to avoid Celery broker requirement
    monkeypatch.setenv("COVERAGE_FORCE_SYNC", "true")


def _headers():
    return {"X-API-Key": "dev-internal-key"}


def test_expand_coverage_sync_success():
    client = TestClient(app)
    r = client.post("/assistant/expand_coverage", headers=_headers(), json={"topics": ["health"]})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"


def test_expand_coverage_invalid_params():
    client = TestClient(app)
    # Payload missing expected keys is still accepted but should not error
    r = client.post("/assistant/expand_coverage", headers=_headers(), json=None)
    assert r.status_code == 200
    assert r.json()["status"] in {"completed", "queued"}


def test_expand_coverage_unauthorized():
    client = TestClient(app)
    r = client.post("/assistant/expand_coverage", json={"topics": []})
    assert r.status_code == 401 or r.status_code == 400


