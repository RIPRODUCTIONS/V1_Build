import json
import types
import pytest


class _FakeVault:
    def __init__(self, token: str | None = "token", refresh: str | None = None):
        self._blob = json.dumps({"access_token": token, "refresh_token": refresh, "expires_at": 0}) if token else None
    def get(self, user_id: str, integ: str, key: str):
        return self._blob
    def put(self, user_id: str, integ: str, key: str, value: str):
        self._blob = value


@pytest.mark.asyncio
async def test_calendar_create_event_success(monkeypatch):
    import app.integrations.google_workspace as gw

    # Fake vault credentials
    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t", refresh="r")))

    # Stub Prometheus Counter to avoid duplicate registration across tests
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

    # Mock httpx AsyncClient.post to return 200 with id
    class _Resp:
        status_code = 200
        def json(self):
            return {"id": "evt1", "htmlLink": "http://example"}
    class _Client:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return False
        async def post(self, *a, **k):
            return _Resp()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=20: _Client())

    cal = gw.GoogleCalendarIntegration()
    res = await cal.create_event("u1", "Standup", "2024-01-01T10:00:00+00:00", "2024-01-01T10:30:00+00:00", "UTC")
    assert res["status"] == "ok" and res["id"] == "evt1"


@pytest.mark.asyncio
async def test_calendar_create_event_rate_limit_retry(monkeypatch):
    import app.integrations.google_workspace as gw

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t", refresh=None)))

    # Stub Prometheus Counter
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

    class _Resp429:
        def __init__(self, code): self.status_code = code; self.text = "rl"
        def json(self): return {}
    class _Client:
        def __init__(self): self.calls = 0
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, *a, **k):
            self.calls += 1
            # First 429, second 200
            if self.calls == 1:
                return _Resp429(429)
            class _OK:
                status_code = 200
                def json(self): return {"id": "evt2", "htmlLink": "x"}
            return _OK()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=20: _Client())

    cal = gw.GoogleCalendarIntegration()
    res = await cal.create_event("u1", "Standup", "2024-01-01T10:00:00+00:00", "2024-01-01T10:30:00+00:00")
    assert res["status"] == "ok" and res["id"] == "evt2"


@pytest.mark.asyncio
async def test_gmail_list_labels_scope_missing(monkeypatch):
    import app.integrations.google_workspace as gw

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))
    # Stub Prometheus Counter to avoid duplicate metric registration
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

    class _Resp403:
        status_code = 403
        text = "forbidden"
        def json(self): return {}
    class _Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, *a, **k): return _Resp403()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    gm = gw.GmailIntegration()
    res = await gm.list_labels("u1")
    assert res["status"] == "skipped_missing_scope" and res["code"] == 403


@pytest.mark.asyncio
async def test_drive_sync_auth_error(monkeypatch):
    import app.integrations.google_workspace as gw

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))

    class _Resp401:
        status_code = 401
        def json(self): return {}
    class _Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, *a, **k): return _Resp401()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    drv = gw.GoogleDriveIntegration()
    res = await drv.sync("u1")
    assert res["status"] == "auth_error"


@pytest.mark.asyncio
async def test_calendar_sync_disabled(monkeypatch):
    import types as _types
    import app.integrations.google_workspace as gw

    # Settings with sync disabled
    monkeypatch.setattr(gw, "get_settings", lambda: _types.SimpleNamespace(GOOGLE_CALENDAR_SYNC=False))
    monkeypatch.setattr(gw, "CredentialVault", _types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))
    # Stub Prometheus Counter
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())
    cal = gw.GoogleCalendarIntegration()
    res = await cal.sync("u1")
    assert res["status"] == "disabled"


@pytest.mark.asyncio
async def test_calendar_sync_publishes_events(monkeypatch):
    import types as _types
    import app.integrations.google_workspace as gw

    # Settings with sync enabled
    monkeypatch.setattr(gw, "get_settings", lambda: _types.SimpleNamespace(GOOGLE_CALENDAR_SYNC=True))
    monkeypatch.setattr(gw, "CredentialVault", _types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))
    # Stub Prometheus Counter
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

    # Stub publish to count calls
    calls = {"n": 0}
    async def _pub(user_id, data, context):
        calls["n"] += 1
    monkeypatch.setattr(gw, "publish_calendar_created", _pub)

    cal = gw.GoogleCalendarIntegration()
    # Stub _list_events to return two items
    async def _list(*a, **k):
        return [
            {"summary": "A", "start": {"dateTime": "2024-01-01T00:00:00+00:00"}},
            {"summary": "B", "start": {"dateTime": "2024-01-02T00:00:00+00:00"}},
        ]
    monkeypatch.setattr(cal, "_list_events", _list)

    res = await cal.sync("u1")
    assert res["status"] == "ok" and res["events_synced"] == 2
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_gmail_create_draft_success(monkeypatch):
    import app.integrations.google_workspace as gw

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))

    class _Resp:
        status_code = 200
        def json(self): return {"id": "d1"}
    class _Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, *a, **k): return _Resp()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    gm = gw.GmailIntegration()
    res = await gm.create_draft("u1", "t@e.com", "subj", "body")
    assert res["status"] == "ok" and res["id"] == "d1"


@pytest.mark.asyncio
async def test_gmail_send_email_missing_scope(monkeypatch):
    import app.integrations.google_workspace as gw

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))

    class _Resp:
        status_code = 403
        text = "forbidden"
        def json(self): return {}
    class _Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, *a, **k): return _Resp()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    gm = gw.GmailIntegration()
    res = await gm.send_email("u1", "t@e.com", "s", "b")
    assert res["status"] == "skipped_missing_scope"


@pytest.mark.asyncio
async def test_drive_create_document_success(monkeypatch):
    import app.integrations.google_workspace as gw

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))

    class _Resp:
        status_code = 200
        def json(self): return {"id": "doc1"}
    class _Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, *a, **k): return _Resp()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=20: _Client())

    drv = gw.GoogleDriveIntegration()
    res = await drv.create_document("u1", "Title", "Content")
    assert res["status"] == "ok" and res["id"] == "doc1"


@pytest.mark.asyncio
async def test_drive_quota_exceeded(monkeypatch):
    import app.integrations.google_workspace as gw

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))
    # Stub Prometheus Counter to avoid duplicate registration across tests
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

    class _Resp:
        status_code = 403
        text = "quota exceeded"
        def json(self): return {}
    class _Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, *a, **k): return _Resp()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    drv = gw.GoogleDriveIntegration()
    res = await drv.sync("u1")
    assert res["status"] == "skipped_missing_scope" or res["status"] == "error"


@pytest.mark.asyncio
async def test_gmail_quota_exceeded(monkeypatch):
    import app.integrations.google_workspace as gw

    monkeypatch.setattr(gw, "CredentialVault", types.SimpleNamespace(from_env=lambda: _FakeVault(token="t")))
    # Stub Prometheus Counter to avoid duplicate registration
    class _FakeCounter:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            return None
    monkeypatch.setattr(gw, "Counter", lambda *a, **k: _FakeCounter())

    class _Resp:
        status_code = 403
        text = "quota exceeded"
        def json(self): return {}
    class _Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, *a, **k): return _Resp()
    monkeypatch.setattr(gw.httpx, "AsyncClient", lambda timeout=10: _Client())

    gm = gw.GmailIntegration()
    res = await gm.list_labels("u1")
    assert res["status"] in {"skipped_missing_scope", "error"}


