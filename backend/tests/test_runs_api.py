from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_runs_list_basics():
    r = client.get('/runs?limit=1&offset=0&sort=created_desc')
    assert r.status_code == 200
    body = r.json()
    assert 'items' in body
