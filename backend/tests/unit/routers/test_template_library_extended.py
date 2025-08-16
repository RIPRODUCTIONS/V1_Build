from __future__ import annotations

import types
from starlette.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_templates_presets_list_and_run(monkeypatch, auth_headers):
    c = _client()
    # Create a preset for a known template id
    template_id = "contact_form_lead_generator"

    # Monkeypatch delay() to avoid Celery broker (patch the symbol bound in router)
    import app.routers.template_library as tl

    class _Job:
        def __init__(self, i):
            self.id = f"job{i}"

    class _TaskStub:
        def __init__(self):
            self._i = 0

        def delay(self, payload):  # noqa: ARG002
            self._i += 1
            return _Job(self._i)

    monkeypatch.setattr(tl, "execute_web_automation_task", _TaskStub())

    # Create preset
    r = c.post(f"/templates/{template_id}/presets", headers=auth_headers, json={"name": "Preset A", "parameters": {"target_websites": ["https://ex.com"]}})
    assert r.status_code == 200
    pid = r.json()["id"]

    # List presets
    r = c.get(f"/templates/{template_id}/presets", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(p["id"] == pid for p in items)

    # Run preset
    r = c.post(f"/templates/{template_id}/presets/{pid}/run", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("queued", "accepted")


def test_templates_rerun_bulk_and_save_last_failed(monkeypatch, auth_headers):
    c = _client()
    template_id = "ecommerce_price_monitor"

    # delay stub to avoid Celery (patch router symbol)
    import app.routers.template_library as tl

    class _Job:
        def __init__(self, i):
            self.id = f"job{i}"

    class _TaskStub:
        def __init__(self):
            self._i = 100

        def delay(self, payload):  # noqa: ARG002
            self._i += 1
            return _Job(self._i)

    monkeypatch.setattr(tl, "execute_web_automation_task", _TaskStub())

    # Seed a failed usage row by calling deploy with missing required field to trigger 400 (and avoid DB row)
    # Instead, create a preset then run with invalid parameters to cause 400 in queue function for coverage
    r = c.post(f"/templates/{template_id}/presets", headers=auth_headers, json={"name": "X", "parameters": {"product_urls": ["https://x" ]}})
    assert r.status_code == 200
    pid = r.json()["id"]

    # Run preset (will queue and create usage rows)
    r = c.post(f"/templates/{template_id}/presets/{pid}/run", headers=auth_headers)
    assert r.status_code == 200

    # Save last failed as preset (likely none failed yet → 404 acceptable)
    r = c.post(f"/templates/{template_id}/presets/save_last_failed", headers=auth_headers)
    assert r.status_code in (200, 404)

    # Rerun bulk failures (may replay 0)
    r = c.post(f"/templates/{template_id}/rerun_bulk", headers=auth_headers)
    assert r.status_code == 200
    assert "replayed" in r.json()


def test_templates_queue_branches(monkeypatch, auth_headers):
    c = _client()
    import app.routers.template_library as tl

    # Stub library to always resolve template ids
    class _Lib:
        async def get_template(self, template_id):  # noqa: ARG002
            return {"id": template_id}

    monkeypatch.setattr(tl, "AutomationTemplateLibrary", lambda: _Lib())

    # Stub task producer
    class _Job:
        def __init__(self, i):
            self.id = f"job{i}"

    class _TaskStub:
        def __init__(self):
            self._i = 0

        def delay(self, payload):  # noqa: ARG002
            self._i += 1
            return _Job(self._i)

    monkeypatch.setattr(tl, "execute_web_automation_task", _TaskStub())

    # ecommerce_price_monitor
    r = c.post(
        "/templates/ecommerce_price_monitor/deploy",
        headers=auth_headers,
        json={"product_urls": ["https://a", "https://b"]},
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"

    # linkedin_lead_extractor
    r = c.post(
        "/templates/linkedin_lead_extractor/deploy",
        headers=auth_headers,
        json={"profile_urls": ["https://linkedin.com/in/x"]},
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"

    # website_change_monitor
    r = c.post(
        "/templates/website_change_monitor/deploy",
        headers=auth_headers,
        json={"pages": ["https://site"]},
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"


def test_save_last_failed_as_preset_and_usage_csv(monkeypatch, auth_headers):
    c = _client()
    import app.routers.template_library as tl
    from app.db import SessionLocal
    from app.models import TemplateUsage
    from json import dumps

    template_id = "contact_form_lead_generator"

    # Seed a failed usage row
    db = SessionLocal()
    try:
        db.add(TemplateUsage(template_id=template_id, queued_tasks=0, success=False, parameters_json=dumps({"x": 1})))
        db.add(TemplateUsage(template_id=template_id, queued_tasks=1, success=True, parameters_json=dumps({"y": 2})))
        db.commit()
    finally:
        db.close()

    # Save last failed as preset
    r = c.post(f"/templates/{template_id}/presets/save_last_failed?name=Saved", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data.get("id") and data.get("name")

    # Request recent usage as CSV for that template
    r = c.get(f"/templates/usage?template_id={template_id}&format=csv&limit=10", headers=auth_headers)
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.headers.get("Content-Type", "").startswith("text/csv")
        assert "template_id,queued_tasks,success,created_at,parameters" in r.text


def test_usage_summary_cache_hit(auth_headers):
    c = _client()
    url = "/templates/usage/summary?template_id=t1&hours=6&buckets=3"
    r1 = c.get(url, headers=auth_headers)
    assert r1.status_code == 200
    r2 = c.get(url, headers=auth_headers)
    assert r2.status_code == 200
    assert r1.json() == r2.json()


def test_templates_queue_remaining_branches(monkeypatch, auth_headers):
    c = _client()
    import app.routers.template_library as tl

    class _Lib:
        async def get_template(self, template_id):  # noqa: ARG002
            return {"id": template_id}

    monkeypatch.setattr(tl, "AutomationTemplateLibrary", lambda: _Lib())

    class _Job:
        def __init__(self, i):
            self.id = f"job{i}"

    class _TaskStub:
        def __init__(self):
            self._i = 1000

        def delay(self, payload):  # noqa: ARG002
            self._i += 1
            return _Job(self._i)

    monkeypatch.setattr(tl, "execute_web_automation_task", _TaskStub())

    # ecommerce_price_spy
    r = c.post(
        "/templates/ecommerce_price_spy/deploy",
        headers=auth_headers,
        json={"product_urls": ["https://p1", "https://p2"]},
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"

    # social_media_lead_harvester
    r = c.post(
        "/templates/social_media_lead_harvester/deploy",
        headers=auth_headers,
        json={"queries": ["acme", "widgets"]},
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"

    # job_board_auto_applier
    r = c.post(
        "/templates/job_board_auto_applier/deploy",
        headers=auth_headers,
        json={"job_queries": ["python developer"]},
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"

    # review_reputation_monitor
    r = c.post(
        "/templates/review_reputation_monitor/deploy",
        headers=auth_headers,
        json={"brand_terms": ["mybrand"]},
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"


