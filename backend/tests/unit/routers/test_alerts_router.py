import os

import pytest


@pytest.mark.unit
def test_alerts_test_endpoint_secure_mode_with_header(client, auth_headers, monkeypatch):
    # Force secure mode to require API key
    monkeypatch.setenv("SECURE_MODE", "true")

    # Avoid network/email side effects
    from app.routers import alerts as alerts_module
    monkeypatch.setattr(alerts_module, "_post_webhook", lambda *_a, **_k: None)
    monkeypatch.setattr(alerts_module, "_send_email", lambda *_a, **_k: None)

    r = client.post("/alerts/test", headers=auth_headers, json={"message": "hello"})
    assert r.status_code == 200
    assert r.json()["sent"] is True


@pytest.mark.unit
def test_alerts_test_endpoint_secure_mode_with_query_param_token(client, monkeypatch):
    # Secure mode on; pass token via query parameter where router reads it
    monkeypatch.setenv("SECURE_MODE", "true")
    monkeypatch.setenv("INTERNAL_API_KEY", "abc123")

    from app.routers import alerts as alerts_module
    monkeypatch.setattr(alerts_module, "_post_webhook", lambda *_a, **_k: None)
    monkeypatch.setattr(alerts_module, "_send_email", lambda *_a, **_k: None)

    r = client.post("/alerts/test?token=abc123", json={"message": "token ok"}, headers={"X-API-Key": "abc123"})
    assert r.status_code == 200
    assert r.json()["sent"] is True


@pytest.mark.unit
def test_alerts_prometheus_receive_parses_alerts(client, monkeypatch):
    from app.routers import alerts as alerts_module
    monkeypatch.setattr(alerts_module, "_post_webhook", lambda *_a, **_k: None)
    monkeypatch.setattr(alerts_module, "_send_email", lambda *_a, **_k: None)

    body = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "HighErrorRate"},
                "annotations": {"description": "5xx > 5%"},
            }
        ]
    }
    # Secure mode may be on from other tests; include header to satisfy router dependency
    r = client.post("/alerts/prometheus", json=body, headers={"X-API-Key": os.getenv("INTERNAL_API_KEY", "test-api-key")})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["received"] == 1


