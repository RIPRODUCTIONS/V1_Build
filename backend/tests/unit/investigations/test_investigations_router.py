from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_get_investigation_not_found(auth_headers):
    c = _client()
    r = c.get("/investigations/not-a-real-task", headers=auth_headers)
    assert r.status_code == 404


def test_recent_limit_bounds(auth_headers):
    c = _client()
    # Should not error with high limit; upper bound enforced internally
    r = c.get("/investigations/recent?limit=9999", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()

