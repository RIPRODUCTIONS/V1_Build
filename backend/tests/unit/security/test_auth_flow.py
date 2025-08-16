import os
import pytest


@pytest.mark.unit
def test_login_and_me_flow(client, monkeypatch):
    # Ensure default admin creds
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin")

    # Login using form-encoded body
    r = client.post("/auth/token", data={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    token = r.json().get("access_token")
    assert token

    # Access /auth/me using bearer token
    r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json().get("username") == "admin"


