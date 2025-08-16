from __future__ import annotations

import json
import types
import pytest

from app.integrations.google_workspace import GmailIntegration


def _seed_token(monkeypatch, token: str = "t"):
    # Seed CredentialVault.get to return a simple oauth blob
    import app.integrations.google_workspace as gw

    class _Vault:
        def get(self, user_id: str, name: str, kind: str):  # noqa: ARG002
            return json.dumps({"access_token": token, "refresh_token": None, "expires_at": 0})

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _Vault()))


@pytest.mark.asyncio
async def test_gmail_list_and_create_label_success(monkeypatch):
    _seed_token(monkeypatch)

    # Mock httpx.AsyncClient.get/post
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
            assert url.endswith("/labels")
            return _Resp(200, {"labels": [{"id": "LBL1", "name": "Inbox"}]})

        async def post(self, *args, **kwargs):  # noqa: ANN002
            return _Resp(200, {"id": "LBLX", "name": "Projects"})

    import app.integrations.google_workspace as gw
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    g = GmailIntegration()
    ls = await g.list_labels("1")
    assert ls["status"] == "ok" and isinstance(ls.get("labels"), list)

    cr = await g.create_label("1", "Projects")
    assert cr["status"] == "ok" and cr["label"]["name"] == "Projects"


@pytest.mark.asyncio
async def test_gmail_modify_and_move_labels(monkeypatch):
    _seed_token(monkeypatch)

    # Sequence: list_labels -> create_label (if missing) -> modify
    class _Resp:
        def __init__(self, code: int, payload: dict):
            self.status_code = code
            self._payload = payload
            self.text = json.dumps(payload)

        def json(self):
            return self._payload

    class _ClientA:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):  # noqa: ANN002
            return False

        async def get(self, url, headers=None, params=None):  # noqa: ANN001, ARG002
            return _Resp(200, {"labels": [{"id": "INBOX", "name": "INBOX"}]})

        async def post(self, url, headers=None, json=None):  # noqa: ANN001, ARG002
            # create_label path
            if url.endswith("/labels"):
                return _Resp(200, {"id": "LBLNEW", "name": "Work"})
            # modify path
            assert "/messages/xyz/modify" in url
            return _Resp(200, {"id": "xyz", "labelIds": ["LBLNEW"]})

    import app.integrations.google_workspace as gw
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _ClientA())

    g = GmailIntegration()
    out = await g.move_message_to_label("1", "xyz", "Work")
    assert out["status"] == "ok"


