from app.main import app
from starlette.testclient import TestClient


class _User:
    scopes: list[str]

    def __init__(self, scopes: list[str]):
        self.scopes = scopes


def test_selfheal_requires_admin_scope(monkeypatch):
    client = TestClient(app)

    # Force a user with no scopes
    from app.security import deps as security_deps

    monkeypatch.setattr(security_deps, "get_current_user", lambda: _User(scopes=[]))

    assert client.get("/selfheal/health").status_code == 403
    assert client.post("/selfheal/heal").status_code == 403
    assert client.post("/selfheal/rebuild").status_code == 403


def test_selfheal_with_admin_scope(monkeypatch):
    client = TestClient(app)

    from app.security import deps as security_deps
    from app.security.scopes import ADMIN_TASKS

    monkeypatch.setattr(security_deps, "get_current_user", lambda: _User(scopes=[ADMIN_TASKS]))

    r = client.get("/selfheal/health")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1

    r = client.post("/selfheal/heal")
    assert r.status_code == 200
    assert r.json().get("success") is True

    r = client.post("/selfheal/rebuild")
    assert r.status_code == 200
    assert r.json().get("success") is True


