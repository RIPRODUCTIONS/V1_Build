from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app
from app.security.jwt_hs256 import HS256JWT


def _client():
    return TestClient(app)


def test_life_endpoints_queue_and_return(auth_headers):
    c = _client()

    # Create a test JWT token
    jwt_handler = HS256JWT(secret="change-me")
    jwt_token = jwt_handler.mint(subject="test-user-123", ttl_override_seconds=3600)
    jwt_headers = {"Authorization": f"Bearer {jwt_token}"}

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
        r = c.post(path, headers=jwt_headers, json={})
        assert r.status_code == 200
        assert r.json().get("status") == "queued"


