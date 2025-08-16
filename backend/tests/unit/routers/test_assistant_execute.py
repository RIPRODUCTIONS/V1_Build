import asyncio
import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("SECURE_MODE", "true")
    monkeypatch.setenv("INTERNAL_API_KEY", "dev-internal-key")


def _headers():
    return {"X-API-Key": "dev-internal-key"}


@pytest.mark.asyncio
async def test_execute_calendar_gmail_drive_success(monkeypatch):
    # Patch integration methods to simple async fakes
    from app.routers import assistant as mod

    async def _ok(*args, **kwargs):
        return {"ok": True}

    cal = mod.hub.integrations.get("google_calendar")
    gm = mod.hub.integrations.get("gmail")
    drv = mod.hub.integrations.get("google_drive")

    if cal:
        monkeypatch.setattr(cal, "create_event", _ok)
    if gm:
        monkeypatch.setattr(gm, "create_draft", _ok)
    if drv:
        monkeypatch.setattr(drv, "create_document", _ok)
        monkeypatch.setattr(drv, "create_text_file", _ok)

    client = TestClient(app)
    intent = "create calendar event 'Standup' tomorrow and draft email about status and create document 'Notes' with content"
    r = client.post("/assistant/execute", headers=_headers(), params={"intent": intent})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("results"), list)
    # Expect at least one action recorded
    assert any(x.get("action", "").startswith("calendar.") for x in data["results"]) or any(
        x.get("action", "").startswith("gmail.") for x in data["results"]
    ) or any(x.get("action", "").startswith("drive.") for x in data["results"])


def test_execute_handler_error(monkeypatch):
    from app.routers import assistant as mod

    async def _boom(*args, **kwargs):
        raise RuntimeError("fail")

    cal = mod.hub.integrations.get("google_calendar")
    if cal:
        monkeypatch.setattr(cal, "create_event", _boom)

    client = TestClient(app)
    intent = "calendar event 'Test'"
    r = client.post("/assistant/execute", headers=_headers(), params={"intent": intent})
    assert r.status_code == 200
    data = r.json()
    # Error should be captured into payload
    assert "error" in data


def test_expand_coverage_delay_failure_falls_back_to_sync(monkeypatch):
    # Ensure not using force-sync env
    monkeypatch.setenv("COVERAGE_FORCE_SYNC", "false")
    # Patch task.delay to raise and task body to return deterministic result
    import app.tasks.coverage_tasks as tasks

    class _Job:
        id = "job123"

    def _expand(body):
        return {"topics": body.get("topics")}

    def _delay(_):
        raise RuntimeError("broker down")

    monkeypatch.setattr(tasks, "expand_coverage", _expand)
    # Attach a temporary object with delay raising
    class _Expand:
        def __call__(self, body):
            return _expand(body)
        def delay(self, body):
            return _delay(body)

    monkeypatch.setattr(tasks, "expand_coverage", _Expand())

    client = TestClient(app)
    r = client.post("/assistant/expand_coverage", headers=_headers(), json={"topics": ["x"]})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert data["result"]["topics"] == ["x"]


