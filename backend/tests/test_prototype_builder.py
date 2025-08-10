# ruff: noqa: I001
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_run_prototype_build():
    r = client.post(
        "/prototype/run",
        json={"name": "Demo", "prompt": "Build a hello world", "repo_dir": None},
    )
    assert r.status_code in (200, 201, 202)
    body = r.json()
    assert body["status"] == "queued"
    assert body["run_id"]
