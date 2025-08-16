from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_osint_run_fallback_and_reports(monkeypatch, auth_headers):
    # Force router to take fallback path (apply()) instead of delay()
    from app.tasks import investigation_tasks as it

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(it.run_osint_dossier, "delay", _raise)

    c = _client()
    payload = {"subject": {"name": "John Example"}}
    r = c.post("/investigations/osint/run", json=payload, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    # In fallback we expect completed with a synthetic task id and embedded result
    assert body["status"] == "completed"
    assert isinstance(body.get("task_id"), str)
    assert body.get("result", {}).get("success") is True

    task_id = body["task_id"]

    # Report generation should return 501 (report builder not available in tests)
    r = c.get(f"/investigations/osint/report/{task_id}", headers=auth_headers)
    assert r.status_code in (200, 501)
    # Artifacts derived from result_summary_json
    r = c.get(f"/investigations/osint/entities/{task_id}.json", headers=auth_headers)
    assert r.status_code == 200
    assert "entities" in r.json()

    r = c.get(f"/investigations/osint/timeline/{task_id}.csv", headers=auth_headers)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/csv")


def test_investigation_artifacts_not_found(auth_headers):
    c = _client()
    r = c.get("/investigations/malware/iocs/does-not-exist.json", headers=auth_headers)
    assert r.status_code == 404
    r = c.get("/investigations/forensics/events/does-not-exist.csv", headers=auth_headers)
    assert r.status_code == 404


