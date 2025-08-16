from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app


def test_metrics_endpoint_available():
    c = TestClient(app)
    r = c.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    # Assert basic Prometheus format and one of our custom metrics
    assert "# HELP" in r.text
    assert "http_request_duration_seconds" in r.text


