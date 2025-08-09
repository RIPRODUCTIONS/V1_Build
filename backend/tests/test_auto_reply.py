from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def test_auto_reply_basic():
    res = client.post("/auto-reply/suggest", json={"body": "Let's schedule a meeting"})
    assert res.status_code == 200
    assert "schedule" in res.json()["reply"].lower()


def test_auto_reply_requires_body():
    res = client.post("/auto-reply/suggest", json={"body": "  "})
    assert res.status_code == 400
