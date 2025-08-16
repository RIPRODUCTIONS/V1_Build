from fastapi.testclient import TestClient
from app.main import create_app


def test_health_and_agent_run():
    app = create_app()
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    r2 = client.post("/ai/agents/run", json={"name": "default", "goal": "smoke", "context": {}})
    assert r2.status_code == 200
from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
