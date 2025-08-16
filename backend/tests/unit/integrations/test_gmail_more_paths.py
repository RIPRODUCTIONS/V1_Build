from __future__ import annotations

import json
import types
import pytest


def _seed(monkeypatch, token: str = "t"):
    import app.integrations.google_workspace as gw

    class _Vault:
        def get(self, user_id: str, name: str, kind: str):  # noqa: ARG002
            return json.dumps({"access_token": token, "refresh_token": None, "expires_at": 0})

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _Vault()))
    return gw


@pytest.mark.asyncio
async def test_gmail_list_messages_and_modify_errors(monkeypatch):
    gw = _seed(monkeypatch)

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

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def get(self, url, headers=None, params=None):  # noqa: ANN001, ARG002
            return _Resp(400, {"error": {"code": 400}})

        async def post(self, url, headers=None, json=None):  # noqa: ANN001, ARG002
            return _Resp(401, {"error": {"code": 401}})

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    api = gw.GmailIntegration()
    out = await api.list_messages("u1", q="from:a@b.com")
    assert out["status"] == "error" and out["code"] == 400

    out2 = await api.modify_message_labels("u1", "mid", add_labels=["L1"])  # returns 401
    assert out2["status"] == "error" and out2["code"] == 401

