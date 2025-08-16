from __future__ import annotations

from prometheus_client import REGISTRY, Counter, Histogram


def _get_or_create_counter(name: str, documentation: str, labelnames: tuple[str, ...] | list[str] = ()):  # type: ignore[override]
    existing = REGISTRY._names_to_collectors.get(name)  # type: ignore[attr-defined]
    if existing is not None:
        return existing  # type: ignore[return-value]
    return Counter(name, documentation, labelnames)


def _get_or_create_histogram(name: str, documentation: str):
    existing = REGISTRY._names_to_collectors.get(name)  # type: ignore[attr-defined]
    if existing is not None:
        return existing  # type: ignore[return-value]
    return Histogram(name, documentation)


automation_tasks_started = _get_or_create_counter(
    "web_automation_tasks_started",
    "Count of started web automation tasks",
)
automation_tasks_completed = _get_or_create_counter(
    "web_automation_tasks_completed",
    "Count of completed web automation tasks",
    ["status"],
)
automation_task_duration_s = _get_or_create_histogram(
    "web_automation_task_duration_seconds",
    "Duration of web automation tasks",
)

automation_actions_total = _get_or_create_counter(
    "web_automation_actions_total",
    "Count of web automation actions attempted",
    ["action"],
)

automation_action_errors_total = _get_or_create_counter(
    "web_automation_action_errors_total",
    "Count of web automation action errors",
    ["action"],
)


