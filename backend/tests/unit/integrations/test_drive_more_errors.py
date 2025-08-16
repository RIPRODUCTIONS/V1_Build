from __future__ import annotations

import json
import types
import pytest


@pytest.mark.asyncio
async def test_drive_create_text_non_json_error(monkeypatch):
    import app.integrations.google_workspace as gw

    class _Vault:
        def get(self, user_id: str, name: str, kind: str):  # noqa: ARG002
            return json.dumps({"access_token": "t", "refresh_token": None, "expires_at": 0})

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _Vault()))

    class _Resp:
        def __init__(self, code: int, text: str):
            self.status_code = code
            self.text = text

        def json(self):  # raise to simulate malformed body
            raise ValueError("bad json")

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def post(self, url, headers=None, content=None, json=None):  # noqa: ANN001, ARG002
            return _Resp(500, "oops")

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=20: _Client())

    drive = gw.GoogleDriveIntegration()
    out = await drive.create_text_file("u1", "a.txt", "hi")
    assert out["status"] == "error" and out["code"] == 500

