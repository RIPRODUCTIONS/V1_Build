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
async def test_gmail_send_and_draft_scope_missing(monkeypatch):
    gw = _seed(monkeypatch)

    class _Resp:
        def __init__(self, code: int):
            self.status_code = code
            self.text = "{}"

        def json(self):
            return {}

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001, ARG002
            return _Resp(403)

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    api = gw.GmailIntegration()
    out = await api.send_email("u1", "a@b.com", "s", "b")
    assert out["status"] == "skipped_missing_scope"
    out2 = await api.create_draft("u1", "a@b.com", "s", "b")
    assert out2["status"] == "skipped_missing_scope"


@pytest.mark.asyncio
async def test_gmail_get_draft_message_id_404(monkeypatch):
    gw = _seed(monkeypatch)

    class _Resp:
        def __init__(self, code: int):
            self.status_code = code
            self.text = "not found"

        def json(self):
            return {}

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def get(self, url, headers=None):  # noqa: ANN001, ARG002
            return _Resp(404)

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    api = gw.GmailIntegration()
    out = await api.get_draft_message_id("u1", "d1")
    assert out["status"] == "error" and out["code"] == 404


