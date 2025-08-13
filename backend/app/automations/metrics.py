from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge

automation_events_processed = Counter(
    "automation_events_processed_total",
    "Total events processed",
    labelnames=("event_type", "status"),
)

automation_rule_executions = Counter(
    "automation_rule_executions_total",
    "Rule executions",
    labelnames=("rule_name", "status"),
)

automation_rule_latency = Histogram(
    "automation_rule_latency_seconds",
    "Time to execute rule",
    labelnames=("rule_name",),
)

active_automation_rules = Gauge(
    "active_automation_rules",
    "Number of active rules",
    labelnames=("user_id",),
)


