import os

import pytest


def _set_ci_env(monkeypatch: pytest.MonkeyPatch, token: str = "test-ci-token") -> str:
    monkeypatch.setenv("CI_ENV", "true")
    monkeypatch.setenv("CI_CLEANUP_TOKEN", token)
    return token


def _ci_headers(token: str) -> dict[str, str]:
    return {"X-CI-Token": token}


@pytest.mark.unit
def test_admin_requires_token(client, monkeypatch: pytest.MonkeyPatch):
    token = _set_ci_env(monkeypatch)

    # Missing header
    r = client.get("/admin/integrations/status")
    assert r.status_code == 401

    # Invalid token
    r = client.get("/admin/integrations/status", headers=_ci_headers("wrong"))
    assert r.status_code == 401

    # Valid token
    r = client.get("/admin/integrations/status", headers=_ci_headers(token))
    assert r.status_code == 200
    payload = r.json()
    assert "integrations" in payload
    assert isinstance(payload["integrations"], list)


@pytest.mark.unit
def test_admin_rate_limit_cleanup_leads(client, monkeypatch: pytest.MonkeyPatch):
    # Isolate by IP and reset in-memory hit counter
    from app.routers import admin as admin_module

    admin_module._ip_to_hits.clear()
    token = _set_ci_env(monkeypatch)
    headers = {**_ci_headers(token), "X-Forwarded-For": "1.2.3.4"}

    # Within limit
    for _ in range(5):
        r = client.delete("/admin/cleanup/leads", headers=headers)
        assert r.status_code in (204, 200)

    # Exceed limit
    r = client.delete("/admin/cleanup/leads", headers=headers)
    assert r.status_code == 429


@pytest.mark.unit
def test_admin_templates_crud_and_roi(client, monkeypatch: pytest.MonkeyPatch):
    token = _set_ci_env(monkeypatch)
    headers = _ci_headers(token)

    # Create/Upsert
    tpl = {
        "id": "tmpl-research-quick",
        "name": "Research Quick",
        "description": "Quick research template",
        "category": "research",
        "difficulty": "easy",
        "estimated_time_minutes": 3,
        "price_per_run_usd": 0.05,
    }
    r = client.post("/admin/templates", headers=headers, json=tpl)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # List
    r = client.get("/admin/templates", headers=headers)
    assert r.status_code == 200
    arr = r.json()
    assert any(x["id"] == tpl["id"] for x in arr)

    # ROI should succeed even if there is no usage yet
    r = client.get("/admin/templates/roi", headers=headers)
    assert r.status_code == 200
    roi = r.json()
    assert "roi" in roi and isinstance(roi["roi"], list)

    # Delete
    r = client.delete(f"/admin/templates/{tpl['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["deleted"] is True


@pytest.mark.unit
def test_admin_tasks_list(client, monkeypatch: pytest.MonkeyPatch):
    token = _set_ci_env(monkeypatch)
    headers = _ci_headers(token)
    r = client.get("/admin/tasks?limit=1", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


