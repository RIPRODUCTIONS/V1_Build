from __future__ import annotations

from prometheus_client import Counter, Histogram


automation_tasks_started = Counter(
    "web_automation_tasks_started",
    "Count of started web automation tasks",
)
automation_tasks_completed = Counter(
    "web_automation_tasks_completed",
    "Count of completed web automation tasks",
    ["status"],
)
automation_task_duration_s = Histogram(
    "web_automation_task_duration_seconds",
    "Duration of web automation tasks",
)

automation_actions_total = Counter(
    "web_automation_actions_total",
    "Count of web automation actions attempted",
    ["action"],
)

automation_action_errors_total = Counter(
    "web_automation_action_errors_total",
    "Count of web automation action errors",
    ["action"],
)


