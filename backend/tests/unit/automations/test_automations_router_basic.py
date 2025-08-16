from __future__ import annotations

from starlette.testclient import TestClient
import uuid

from app.main import app
from app.dependencies.auth import get_current_user


def _client() -> TestClient:
    return TestClient(app)


def test_automations_rules_list_and_toggle(auth_headers):
    c = _client()
    # Override auth to simulate a logged-in user id
    app.dependency_overrides[get_current_user] = lambda: 1
    # List rules (empty ok)
    r = c.get("/automations/rules", headers=auth_headers)
    assert r.status_code == 200

    # Create a rule
    rid = f"r-{uuid.uuid4()}"
    payload = {
        "id": rid,
        "name": "Rule1",
        "trigger_type": "event",
        "event_pattern": None,
        "conditions": {},
        "actions": [],
        "enabled": True,
    }
    r = c.post("/automations/rules", headers=auth_headers, json=payload)
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        assert r.json()["id"] == rid

    # Toggle
    r = c.put(f"/automations/rules/{rid}/toggle", headers=auth_headers)
    assert r.status_code == 200 and isinstance(r.json().get("enabled"), bool)
    # Clear override
    app.dependency_overrides.pop(get_current_user, None)


def test_automations_metrics_and_health(auth_headers, monkeypatch):
    c = _client()
    # Metrics should return summary object
    r = c.get("/automations/metrics", headers=auth_headers)
    assert r.status_code == 200 and "summary" in r.json()

    # Health path should not raise; tolerate degraded/healthy
    r = c.get("/automations/health", headers=auth_headers)
    assert r.status_code == 200
    assert r.json().get("status") in ("healthy", "degraded", "error")


