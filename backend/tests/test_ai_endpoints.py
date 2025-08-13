from app.main import app
from starlette.testclient import TestClient


class _User:
    scopes: list[str]

    def __init__(self, scopes: list[str]):
        self.scopes = scopes


def test_ai_scopes(monkeypatch):
    client = TestClient(app)

    from app.security import deps as security_deps
    from app.security.scopes import READ_LEADS, WRITE_AI

    # historical requires READ_LEADS
    monkeypatch.setattr(security_deps, "get_current_user", lambda: _User(scopes=[]))
    assert client.post("/ai/historical/ingest_and_analyze", json={}).status_code == 403

    monkeypatch.setattr(security_deps, "get_current_user", lambda: _User(scopes=[READ_LEADS]))
    assert client.post("/ai/historical/ingest_and_analyze", json={"user_id": "u"}).status_code == 200

    # behavior and predict require WRITE_AI
    monkeypatch.setattr(security_deps, "get_current_user", lambda: _User(scopes=[]))
    assert client.post("/ai/behavior/analyze", json={}).status_code == 403
    assert client.post("/ai/predict/automate", json={}).status_code == 403

    monkeypatch.setattr(security_deps, "get_current_user", lambda: _User(scopes=[WRITE_AI]))
    assert client.post("/ai/behavior/analyze", json={"user_id": "u"}).status_code == 200
    assert client.post("/ai/predict/automate", json={"user_id": "u"}).status_code == 200


