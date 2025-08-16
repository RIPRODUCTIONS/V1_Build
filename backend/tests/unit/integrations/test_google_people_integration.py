from __future__ import annotations

import json
import types
import pytest

from app.integrations.google_workspace import GooglePeopleIntegration


def _seed_token(monkeypatch, token: str = "t"):
    import app.integrations.google_workspace as gw

    class _Vault:
        def get(self, user_id: str, name: str, kind: str):  # noqa: ARG002
            return json.dumps({"access_token": token, "refresh_token": None, "expires_at": 0})

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _Vault()))


@pytest.mark.asyncio
async def test_people_list_contacts_success(monkeypatch):
    _seed_token(monkeypatch)

    class _Resp:
        def __init__(self, code: int, payload: dict):
            self.status_code = code
            self._payload = payload
            self.text = json.dumps(payload)

        def json(self):
            return self._payload

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):  # noqa: ANN002
            return False

        async def get(self, url, headers=None, params=None):  # noqa: ANN001, ARG002
            assert "people/me/connections" in url
            return _Resp(200, {"connections": [{"names": [{"displayName": "John"}]}, {"names": [{"displayName": "Jane"}]}]})

    import app.integrations.google_workspace as gw
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    class _GP(GooglePeopleIntegration):
        async def sync(self, user_id: str):  # type: ignore[override]
            return {"status": "ok"}

    api = _GP()
    out = await api.list_contacts("1")
    assert out["status"] == "ok"
    assert isinstance(out.get("connections"), list)


@pytest.mark.asyncio
async def test_people_create_contact_success(monkeypatch):
    _seed_token(monkeypatch)

    class _Resp:
        def __init__(self, code: int, payload: dict):
            self.status_code = code
            self._payload = payload
            self.text = json.dumps(payload)

        def json(self):
            return self._payload

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):  # noqa: ANN002
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001, ARG002
            assert url.endswith("people:createContact")
            return _Resp(200, {"resourceName": "people/123"})

    import app.integrations.google_workspace as gw
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())


@pytest.mark.asyncio
async def test_people_list_contacts_auth_error(monkeypatch):
    _seed_token(monkeypatch)

    class _Resp:
        def __init__(self, code: int, payload: dict):
            self.status_code = code
            self._payload = payload
            self.text = json.dumps(payload)

        def json(self):
            return self._payload

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):  # noqa: ANN002
            return False

        async def get(self, url, headers=None, params=None):  # noqa: ANN001, ARG002
            return _Resp(403, {"error": {"code": 403}})
        async def post(self, url, headers=None, json=None):  # noqa: ANN001, ARG002
            return _Resp(403, {"error": {"code": 403}})

    import app.integrations.google_workspace as gw
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    class _GP(GooglePeopleIntegration):
        async def sync(self, user_id: str):  # type: ignore[override]
            return {"status": "ok"}

    api = _GP()
    out = await api.list_contacts("1")
    assert out["status"] == "skipped_missing_scope"

    class _GP(GooglePeopleIntegration):
        async def sync(self, user_id: str):  # type: ignore[override]
            return {"status": "ok"}

    api = _GP()
    out = await api.create_contact("1", name="Alice", email="alice@example.com")
    assert out["status"] == "skipped_missing_scope"


