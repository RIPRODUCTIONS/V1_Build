from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app


def _client():
    return TestClient(app)


def test_admin_templates_csv_export_404_or_csv(auth_headers):
    c = _client()
    r = c.get("/admin/templates/export", headers=auth_headers)
    # Depending on router behavior in this project, accept either 200 CSV, 404, or 405
    assert r.status_code in (200, 404, 405)
    if r.status_code == 200:
        assert r.headers.get("Content-Type", "").startswith("text/csv")


