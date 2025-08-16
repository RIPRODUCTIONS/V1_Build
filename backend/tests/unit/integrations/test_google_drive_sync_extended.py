from __future__ import annotations

import json
import types

import pytest

from app.integrations.google_workspace import GoogleDriveIntegration


def _seed_token(monkeypatch, token: str = "t"):
    import app.integrations.google_workspace as gw

    class _Vault:
        def get(self, user_id: str, name: str, kind: str):  # noqa: ARG002
            return json.dumps({"access_token": token, "refresh_token": None, "expires_at": 0})

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _Vault()))


@pytest.mark.asyncio
async def test_drive_sync_success_with_files(monkeypatch):
    _seed_token(monkeypatch)
    # Stub Prometheus Counter to avoid duplicate registration
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    import app.integrations.google_workspace as gw
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

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
            return _Resp(200, {"files": [{"id": "1", "name": "Doc"}]})

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    api = GoogleDriveIntegration()
    out = await api.sync("1")
    assert out["status"] == "ok" and out["files_indexed"] == 1


@pytest.mark.asyncio
async def test_drive_sync_empty(monkeypatch):
    _seed_token(monkeypatch)
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    import app.integrations.google_workspace as gw
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

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
            return _Resp(200, {"files": []})

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    api = GoogleDriveIntegration()
    out = await api.sync("1")
    assert out["status"] == "ok" and out["files_indexed"] == 0


@pytest.mark.asyncio
async def test_drive_sync_network_error(monkeypatch):
    _seed_token(monkeypatch)
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    import app.integrations.google_workspace as gw
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):  # noqa: ANN002
            return False

        async def get(self, url, headers=None, params=None):  # noqa: ANN001, ARG002
            raise RuntimeError("network down")

    monkeypatch.setattr(gw, "httpx", types.SimpleNamespace(AsyncClient=lambda timeout=10: _Client()))

    api = GoogleDriveIntegration()
    import pytest as _pytest
    with _pytest.raises(RuntimeError):
        await api.sync("1")


