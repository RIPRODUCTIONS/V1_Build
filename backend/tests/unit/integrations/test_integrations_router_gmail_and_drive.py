from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_gmail_router_missing_integration(auth_headers, monkeypatch):
    # Ensure google integrations are not registered
    import app.integrations.router as ir
    ir.hub.integrations.pop("gmail", None)

    c = _client()
    r = c.post(
        "/integrations/google/gmail/send/u1",
        headers=auth_headers,
        json={"to": "a@b.com", "subject": "s", "body": "hi"},
    )
    assert r.status_code == 200 and r.json().get("status") == "missing_integration"


def test_gmail_router_send_and_draft_happy_paths(auth_headers, monkeypatch):
    import types
    import app.integrations.router as ir

    class _Gmail:
        async def send_email(self, user_id, to, subject, body):  # noqa: ANN001
            return {"status": "ok", "id": "m1"}

        async def create_draft(self, user_id, to, subject, body):  # noqa: ANN001
            return {"status": "ok", "id": "d1"}

        async def get_draft_message_id(self, user_id, draft_id):  # noqa: ANN001
            return {"status": "ok", "message_id": "m1"}

        async def move_message_to_label(self, user_id, message_id, label):  # noqa: ANN001
            return {"status": "ok"}

    ir.hub.integrations["gmail"] = _Gmail()

    c = _client()
    r = c.post(
        "/integrations/google/gmail/send/u1",
        headers=auth_headers,
        json={"to": "a@b.com", "subject": "s", "body": "hi"},
    )
    assert r.status_code == 200 and r.json().get("status") == "ok"

    r = c.post(
        "/integrations/google/gmail/draft/u1",
        headers=auth_headers,
        json={"to": "a@b.com", "subject": "s", "body": "hi"},
    )
    assert r.status_code == 200 and r.json().get("status") == "ok"

    r = c.post(
        "/integrations/google/gmail/move_draft/u1",
        headers=auth_headers,
        json={"draft_id": "d1", "label": "X"},
    )
    assert r.status_code == 200 and r.json().get("status") == "ok"


def test_drive_create_text_and_doc_errors(auth_headers, monkeypatch):
    import json
    import app.integrations.google_workspace as gw

    class _Vault:
        def get(self, user_id: str, name: str, kind: str):  # noqa: ARG002
            return json.dumps({"access_token": "t", "refresh_token": None, "expires_at": 0})

    monkeypatch.setattr(gw, "CredentialVault", type("V", (), {"from_env": staticmethod(lambda: _Vault())}))

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

        async def post(self, url, headers=None, content=None, json=None):  # noqa: ANN001, ARG002
            return _Resp(403, {"error": {"code": 403}})

    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=20: _Client())

    drive = gw.GoogleDriveIntegration()
    out1 = app_run(drive.create_text_file("u1", "a.txt", "hi"))
    out2 = app_run(drive.create_document("u1", "Doc", "hi"))
    assert out1["status"] == "skipped_missing_scope" and out2["status"] == "skipped_missing_scope"


def app_run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


