from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_integrations_router_missing_integration(auth_headers):
    c = _client()
    r = c.post("/integrations/google/calendar/create/u1", headers=auth_headers, json={"summary": "x", "start_iso": "2024-01-01T00:00:00+00:00", "end_iso": "2024-01-01T01:00:00+00:00"})
    assert r.status_code == 200
    assert r.json().get("status") == "missing_integration"


def test_integrations_router_mock_calendar_happy(auth_headers):
    c = _client()
    # Discover should include mock_calendar
    r = c.get("/integrations/discover/u1", headers=auth_headers)
    assert r.status_code == 200
    assert "integrations" in r.json()
    # Test mock via /test endpoint
    r = c.get("/integrations/test/u1", headers=auth_headers)
    assert r.status_code == 200
    assert r.json().get("source") in ("mock", None)


