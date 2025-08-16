from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, Info, Summary

task_counter = Counter(
    "tasks_total", "Total tasks processed", ["tenant_id", "domain", "agent_id", "status"]
)

task_duration = Histogram(
    "task_duration_seconds",
    "Task processing duration",
    ["tenant_id", "domain", "agent_id"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
)

queue_depth = Gauge("queue_depth", "Current queue depth", ["tenant_id", "domain", "priority"])
dlq_size = Gauge("dlq_size", "Dead letter queue size", ["tenant_id", "domain"])

active_workers = Gauge("active_workers", "Active workers", ["domain"])
worker_task_rate = Summary("worker_task_rate", "Tasks per worker", ["domain", "worker_id"])

rate_limit_hits = Counter(
    "rate_limit_hits_total", "Rate limit violations", ["tenant_id", "domain", "agent_id", "limit_type"]
)

api_requests = Counter(
    "api_requests_total", "API requests", ["tenant_id", "endpoint", "method", "status"]
)
api_duration = Histogram("api_request_duration_seconds", "API request duration", ["tenant_id", "endpoint", "method"])

webhook_requests = Counter(
    "webhook_requests_total", "Webhook requests", ["tenant_id", "endpoint", "status", "validation_result"]
)
webhook_processing_time = Histogram("webhook_processing_seconds", "Webhook processing duration", ["tenant_id", "endpoint"])

sla_breaches = Counter(
    "sla_breaches_total", "SLA breaches by type", ["tenant_id", "domain", "agent_id", "breach_type"]
)

external_api_calls = Counter("external_api_calls_total", "External API calls", ["provider", "endpoint", "status"])
external_api_duration = Histogram("external_api_duration_seconds", "External API duration", ["provider", "endpoint"])

system_info = Info("system_info", "System information")
cpu_usage = Gauge("cpu_usage_percent", "CPU usage percentage")
memory_usage = Gauge("memory_usage_bytes", "Memory usage bytes")
disk_usage = Gauge("disk_usage_bytes", "Disk usage bytes")


class MetricsCollector:
    @staticmethod
    def record_task_completion(tenant_id: str, domain: str, agent_id: str, duration: float, status: str):
        task_counter.labels(tenant_id=tenant_id, domain=domain, agent_id=agent_id, status=status).inc()
        task_duration.labels(tenant_id=tenant_id, domain=domain, agent_id=agent_id).observe(duration)

    @staticmethod
    def update_queue_depth(tenant_id: str, domain: str, priority: int, depth: int):
        queue_depth.labels(tenant_id=tenant_id, domain=domain, priority=str(priority)).set(depth)

    @staticmethod
    def record_rate_limit_hit(tenant_id: str, domain: str, agent_id: str, limit_type: str):
        rate_limit_hits.labels(tenant_id=tenant_id, domain=domain, agent_id=agent_id, limit_type=limit_type).inc()

    @staticmethod
    def record_api_request(tenant_id: str, endpoint: str, method: str, status: int, duration: float):
        api_requests.labels(tenant_id=tenant_id, endpoint=endpoint, method=method, status=str(status)).inc()
        api_duration.labels(tenant_id=tenant_id, endpoint=endpoint, method=method).observe(duration)

    @staticmethod
    def record_webhook_request(tenant_id: str, endpoint: str, status: str, validation_result: str, duration: float):
        webhook_requests.labels(tenant_id=tenant_id, endpoint=endpoint, status=status, validation_result=validation_result).inc()
        webhook_processing_time.labels(tenant_id=tenant_id, endpoint=endpoint).observe(duration)

    @staticmethod
    def record_sla_breach(tenant_id: str, domain: str, agent_id: str, breach_type: str):
        sla_breaches.labels(tenant_id=tenant_id, domain=domain, agent_id=agent_id, breach_type=breach_type).inc()







