from __future__ import annotations

import json
import types
import pytest


@pytest.mark.asyncio
async def test_drive_sync_timeout(monkeypatch):
    import app.integrations.google_workspace as gw

    class _Vault:
        def get(self, user_id: str, name: str, kind: str):  # noqa: ARG002
            return json.dumps({"access_token": "t", "refresh_token": None, "expires_at": 0})

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _Vault()))

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):  # noqa: ANN001
            return False

        async def get(self, url, headers=None, params=None):  # noqa: ANN001, ARG002
            raise RuntimeError("timeout")

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    api = gw.GoogleDriveIntegration()
    with pytest.raises(RuntimeError):
        await api.sync("u1")


