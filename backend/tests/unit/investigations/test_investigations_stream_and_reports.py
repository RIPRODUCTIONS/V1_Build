from __future__ import annotations

from typing import Any, Dict

import pytest
from starlette.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_stream_investigation_success_event(monkeypatch, auth_headers):
    # Monkeypatch celery AsyncResult in investigations router to produce a single SUCCESS event
    import app.routers.investigations as inv

    class _Result:
        state = "SUCCESS"

        def get(self, timeout: float = 0) -> Dict[str, Any]:  # noqa: ARG002
            return {"ok": True}

    class _Celery:
        def AsyncResult(self, task_id: str):  # noqa: N802, ARG002
            return _Result()

    monkeypatch.setattr(inv, "celery_app", _Celery())

    c = _client()
    # The stream endpoint requires token via query string or header
    with c.stream(
        "GET",
        "/investigations/stream/t123?token=" + auth_headers["X-API-Key"],
        headers=auth_headers,
    ) as r:
        # Read first chunk
        body = b"".join(list(r.iter_raw()))
    text = body.decode(errors="ignore")
    # Should contain an SSE line with JSON including state SUCCESS or status completed
    assert "data:" in text
    assert "\"state\": \"SUCCESS\"" in text or "\"status\": \"completed\"" in text


def test_malware_and_forensics_reports_501(monkeypatch, auth_headers):
    # Force fallback path for run endpoints so DB records are created
    from app.tasks import investigation_tasks as it

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(it.run_malware_dynamic, "delay", _raise)
    monkeypatch.setattr(it.run_forensics_timeline, "delay", _raise)

    c = _client()

    # Start malware dynamic (fallback to completed with synthetic task id)
    r = c.post("/investigations/malware/dynamic/run", json={"sample": "x.exe"}, headers=auth_headers)
    assert r.status_code == 200
    mid = r.json()["task_id"]

    # Start forensics timeline (fallback)
    r = c.post("/investigations/forensics/timeline/run", json={"source": "evidence.dd"}, headers=auth_headers)
    assert r.status_code == 200
    fid = r.json()["task_id"]

    # Fetch reports; since report builders are not present in tests, expect 501
    r = c.get(f"/investigations/malware/report/{mid}", headers=auth_headers)
    assert r.status_code in (200, 501)
    r = c.get(f"/investigations/forensics/report/{fid}", headers=auth_headers)
    assert r.status_code in (200, 501)


