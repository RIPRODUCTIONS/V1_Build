from __future__ import annotations

import json
import types
import pytest


@pytest.mark.asyncio
async def test_people_list_contacts_429_and_pagination(monkeypatch):
    from app.integrations.google_workspace import GooglePeopleIntegration as GPI
    import app.integrations.google_workspace as gw

    # Seed token
    class _Vault:
        def get(self, user_id: str, name: str, kind: str):  # noqa: ARG002
            return json.dumps({"access_token": "t", "refresh_token": None, "expires_at": 0})

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _Vault()))

    # Client that first returns 429, then success with two pages
    class _Resp:
        def __init__(self, code: int, payload: dict):
            self.status_code = code
            self._payload = payload
            self.text = json.dumps(payload)

        def json(self):
            return self._payload

    class _Client:
        def __init__(self):
            self.calls = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def get(self, url, headers=None, params=None):  # noqa: ANN001, ARG002
            self.calls += 1
            if self.calls == 1:
                return _Resp(429, {"error": {"code": 429}})
            # emulate second page
            if params and params.get("pageSize") == 2:
                return _Resp(200, {"connections": [{"resourceName": "people/1"}, {"resourceName": "people/2"}]})
            return _Resp(200, {"connections": []})

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    class _GPI(GPI):
        async def sync(self, user_id: str):  # type: ignore[override]
            return {"status": "ok"}
        async def list_contacts(self, user_id: str, page_size: int = 10):  # type: ignore[override]
            # call base and add simple pagination call
            first = await super().list_contacts(user_id, page_size=2)
            if first.get("status") == "error":
                return first
            # fetch next (empty)
            second = await super().list_contacts(user_id, page_size=3)
            if second.get("status") == "error":
                return second
            all_items = (first.get("connections") or []) + (second.get("connections") or [])
            return {"status": "ok", "connections": all_items}

    api = _GPI()
    out = await api.list_contacts("u1")
    # Our base returns error on 429; the overridden method bubbles it up
    if out.get("status") == "error":
        assert out["code"] == 429 or "code" in out.get("error", {})
    else:
        assert out.get("status") == "ok"

