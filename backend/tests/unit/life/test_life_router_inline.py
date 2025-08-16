from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app


def _client():
    return TestClient(app)


def test_life_endpoints_queue_and_return(auth_headers):
    c = _client()
    for path in [
        "/life/health/wellness",
        "/life/nutrition/plan",
        "/life/home/evening",
        "/life/transport/commute",
        "/life/learning/upskill",
        "/life/finance/investments",
        "/life/finance/bills",
        "/life/security/sweep",
        "/life/travel/plan",
        "/life/calendar/organize",
        "/life/shopping/optimize",
    ]:
        r = c.post(path, headers=auth_headers, json={})
        assert r.status_code == 200
        assert r.json().get("status") == "queued"


