from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_operator_demo_and_metrics():
    # Hit demo endpoint with operator disabled by default; ensure endpoint responds
    res = client.post(
        "/operator/web/demo/contact_form",
        json={"url": "https://example.com/contact", "form_data": {"name": "A"}},
    )
    assert res.status_code == 200
    body = res.json()
    assert "status" in body

    # Scrape metrics and ensure metric names exist (no strict cardinality check)
    m = client.get("/metrics").text
    assert "web_automation_tasks_started" in m
    assert "web_automation_tasks_completed" in m
    assert "web_automation_actions_total" in m
    assert "web_automation_action_errors_total" in m


