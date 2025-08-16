from __future__ import annotations

from prometheus_client import REGISTRY

from app.web_operator import web_metrics as wm


def test_web_metrics_counters_increment():
    # Ensure collectors are registered once
    before = set(REGISTRY._names_to_collectors.keys())  # type: ignore[attr-defined]
    wm.automation_tasks_started.inc()
    wm.automation_tasks_completed.labels(status="ok").inc()
    wm.automation_actions_total.labels(action="navigate").inc()
    wm.automation_action_errors_total.labels(action="click").inc()
    wm.automation_task_duration_s.observe(0.01)
    after = set(REGISTRY._names_to_collectors.keys())
    assert "web_automation_tasks_started" in after
    assert "web_automation_tasks_completed" in after
    assert after.issuperset(before)


