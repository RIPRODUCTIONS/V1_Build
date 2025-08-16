from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_run_personal_unsupported_template(auth_headers):
    c = _client()
    r = c.post("/personal/run/not_a_template", headers=auth_headers, json={"foo": "bar"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "unsupported"
    assert data["template_id"] == "not_a_template"


def test_finance_import_empty_file(auth_headers):
    c = _client()
    r = c.post(
        "/personal/finance/import_csv",
        headers=auth_headers,
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["parsed"] == 0


def test_twitter_oauth_disabled_when_not_configured(auth_headers):
    c = _client()
    r = c.get("/personal/social/oauth/twitter/start", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") in ("disabled", None)

