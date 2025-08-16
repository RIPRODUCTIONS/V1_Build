import types
import pytest
from starlette.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def app_with_auth(monkeypatch):
    monkeypatch.setenv("SECURE_MODE", "true")
    monkeypatch.setenv("INTERNAL_API_KEY", "dev-internal-key")
    return create_app()


def _headers():
    return {"X-API-Key": "dev-internal-key"}


def test_self_build_scan_and_lifecycle(monkeypatch, app_with_auth):
    # Stub propose_new_templates to produce deterministic proposals
    import app.ai.system_brain as brain

    monkeypatch.setattr(
        brain, "propose_new_templates",
        lambda ctx: [
            {
                "template_id": "auto_contact",
                "name": "Auto Contact",
                "description": "desc",
                "category": "lead_generation",
                "parameters": {"x": 1},
                "score": 0.9,
            }
        ],
    )

    client = TestClient(app_with_auth)

    # Run scan
    r = client.post("/assistant/self_build/scan", headers=_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert isinstance(body.get("proposals"), list)

    # List proposals
    r = client.get("/assistant/self_build/proposals", headers=_headers())
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    pid = items[0]["id"]

    # Approve
    r = client.post(f"/assistant/self_build/proposals/{pid}/approve", headers=_headers())
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # Apply → creates/updates AutomationTemplate
    r = client.post(f"/assistant/self_build/proposals/{pid}/apply", headers=_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data.get("template_id") is not None


def test_self_build_routes_unauthorized(monkeypatch):
    monkeypatch.setenv("SECURE_MODE", "true")
    # No INTERNAL_API_KEY set → should 401
    app = create_app()
    client = TestClient(app)
    r = client.post("/assistant/self_build/scan")
    assert r.status_code in (400, 401, 403)


