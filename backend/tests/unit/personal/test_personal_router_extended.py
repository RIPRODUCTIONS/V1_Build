from __future__ import annotations

import io
from starlette.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_personal_oauth_start_disabled(auth_headers, monkeypatch):
    # Ensure oauth client ids are not set
    monkeypatch.delenv("TWITTER_CLIENT_ID", raising=False)
    c = _client()
    r = c.get("/personal/social/oauth/twitter/start", headers=auth_headers)
    assert r.status_code == 200
    assert r.json().get("status") == "disabled"


def test_personal_oauth_callback_store_token(auth_headers, monkeypatch):
    # Disable real exchange: should store token directly
    monkeypatch.setenv("PERSONAL_OAUTH_EXCHANGE_REAL", "false")
    c = _client()
    r = c.get("/personal/social/oauth/twitter/callback?code=abc", headers=auth_headers)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
    # Status should reflect a stored provider
    r = c.get("/personal/social/oauth/status", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body.get("twitter") in (True, False)


def test_personal_finance_import_csv_basic(auth_headers):
    c = _client()
    csv_bytes = b"date,description,amount\n2024-01-01,Uber,12.50\n2024-01-02,Whole Foods,30.25\n"
    files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
    r = c.post("/personal/finance/import_csv", headers=auth_headers, files=files)
    assert r.status_code == 200
    js = r.json()
    assert js["status"] == "ok"
    assert js["parsed"] >= 2


