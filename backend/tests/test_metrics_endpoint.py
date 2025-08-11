from app.main import app
from starlette.testclient import TestClient


def test_metrics_endpoint():
    c = TestClient(app)
    r = c.get("/metrics")
    assert r.status_code == 200
    assert b"http_requests_total" in r.content or b"process_cpu_seconds_total" in r.content
