from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# HTTP Status Code Constants
HTTP_CLIENT_ERROR = 400
HTTP_SERVER_ERROR = 500


@dataclass
class AgentExecutionMetrics:
    """Container for agent execution metrics data."""

    department: str
    intent: str
    provider: str
    tokens: int
    cost_usd: float
    latency_ms: float


# API SLO Metrics
REQUESTS = Counter(
    "api_requests_total",
    "Total API requests",
    ["route", "method", "status_class"],
)

LATENCY = Histogram(
    "api_request_latency_seconds",
    "API request latency in seconds",
    ["route", "method", "status_class"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
)

ERROR_RATE = Counter(
    "api_errors_total",
    "Total API errors (4xx, 5xx)",
    ["route", "method", "status_code", "error_type"],
)

# Orchestrator Metrics
REDIS_STREAM_LAG = Gauge(
    "redis_stream_lag_seconds",
    "Redis Stream lag in seconds per consumer group",
    ["stream", "consumer_group", "consumer"],
)

REDIS_REPROCESSING_COUNT = Counter(
    "redis_reprocessing_total",
    "Total events reprocessed due to failures",
    ["stream", "consumer_group", "event_type"],
)

# Manager Health Metrics
MANAGER_PLANNING_DURATION = Histogram(
    "manager_planning_duration_seconds",
    "Manager planning duration in seconds",
    ["intent", "department"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)

MANAGER_STEP_COUNT = Histogram(
    "manager_step_count",
    "Number of steps generated per plan",
    ["intent", "department"],
    buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
)

MANAGER_FAILURE_REASONS = Counter(
    "manager_failures_total",
    "Manager failures by reason",
    ["reason", "intent", "department"],
)

# Runs & Status Metrics
RUNS_BY_STATUS = Gauge(
    "runs_by_status",
    "Current count of runs by status",
    ["status", "department"],
)

RUNS_BY_DEPARTMENT = Gauge(
    "runs_by_department",
    "Current count of runs by department",
    ["department"],
)

# Queue Depth Metrics
QUEUE_DEPTH = Gauge(
    "queue_depth",
    "Current queue depth by stream",
    ["stream", "consumer_group"],
)

# Idea Engine & Automation Metrics
IDEA_ENGINE_RUNS = Counter(
    "idea_engine_runs_total",
    "Total Idea Engine runs by pipeline type",
    ["pipeline_type", "status", "department"],
)

IDEA_ENGINE_LATENCY = Histogram(
    "idea_engine_latency_seconds",
    "Idea Engine execution latency in seconds",
    ["pipeline_type", "department"],
    buckets=[0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60],
)

IDEA_ENGINE_IDEAS_GENERATED = Counter(
    "idea_engine_ideas_total",
    "Total business ideas generated",
    ["department", "complexity", "market_size"],
)

AUTOMATION_RUNS_BY_INTENT = Counter(
    "automation_runs_total",
    "Total automation runs by intent",
    ["intent", "department", "status"],
)

AUTOMATION_ARTIFACTS_CREATED = Counter(
    "automation_artifacts_total",
    "Total artifacts created by automation runs",
    ["kind", "department", "status"],
)

# Agent Metrics (for Batch E)
AGENT_TOKENS_TOTAL = Counter(
    "agent_tokens_total",
    "Total tokens consumed by agents",
    ["department", "intent", "provider"],
)

AGENT_COST_USD_TOTAL = Counter(
    "agent_cost_usd_total",
    "Total cost in USD by agents",
    ["department", "intent", "provider"],
)

AGENT_LATENCY_MS = Histogram(
    "agent_latency_ms",
    "Agent execution latency in milliseconds",
    ["department", "intent", "provider"],
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
)

# AI Department Metrics (for Batch E)
AI_DEPARTMENT_RUNS = Counter(
    "ai_department_runs_total",
    "Total AI department runs by department and status",
    ["department", "status"],
)

AI_DEPARTMENT_LATENCY = Histogram(
    "ai_department_latency_seconds",
    "AI department execution latency in seconds",
    ["department"],
    buckets=[0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60],
)

AI_DEPARTMENT_TOKEN_USAGE = Counter(
    "ai_department_token_usage_total",
    "Total token usage by AI departments",
    ["department", "model"],
)

# Autonomous Mode Metrics
AUTONOMOUS_RUNS_TOTAL = Gauge(
    "autonomous_runs_total",
    "Total autonomous runs executed",
    ["status"],
)

AUTONOMOUS_LAST_RUN_TIMESTAMP = Gauge(
    "autonomous_last_run_timestamp",
    "Timestamp of last autonomous run",
    ["department"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        response: Response | None = None

        try:
            response = await call_next(request)
            return response
        finally:
            if response:
                raw_status = int(response.status_code)
                status_class = f"{raw_status // 100}xx"
                method = request.method

                # Get route path
                try:
                    route_obj = request.scope.get("route")
                    route = getattr(route_obj, "path", request.url.path)
                except Exception:
                    route = request.url.path

                # Skip metrics and health endpoints
                if route not in ("/metrics", "/health", "/healthz", "/readyz"):
                    # Record request metrics
                    REQUESTS.labels(route=route, method=method, status_class=status_class).inc()

                    # Record latency
                    duration = time.perf_counter() - start
                    LATENCY.labels(route=route, method=method, status_class=status_class).observe(
                        duration
                    )

                    # Record errors
                    if raw_status >= HTTP_CLIENT_ERROR:
                        error_type = (
                            "client_error" if raw_status < HTTP_SERVER_ERROR else "server_error"
                        )
                        ERROR_RATE.labels(
                            route=route,
                            method=method,
                            status_code=str(raw_status),
                            error_type=error_type,
                        ).inc()


def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint"""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Utility functions for updating metrics
def update_runs_by_status(status: str, department: str, count: int):
    """Update runs by status metric"""
    RUNS_BY_STATUS.labels(status=status, department=department).set(count)


def update_runs_by_department(department: str, count: int):
    """Update runs by department metric"""
    RUNS_BY_DEPARTMENT.labels(department=department).set(count)


def update_queue_depth(stream: str, consumer_group: str, depth: int):
    """Update queue depth metric"""
    QUEUE_DEPTH.labels(stream=stream, consumer_group=consumer_group).set(depth)


def update_redis_stream_lag(stream: str, consumer_group: str, consumer: str, lag_seconds: float):
    """Update Redis Stream lag metric"""
    REDIS_STREAM_LAG.labels(stream=stream, consumer_group=consumer_group, consumer=consumer).set(
        lag_seconds
    )


def record_manager_planning(intent: str, department: str, duration: float, steps: int):
    """Record manager planning metrics"""
    MANAGER_PLANNING_DURATION.labels(intent=intent, department=department).observe(duration)
    MANAGER_STEP_COUNT.labels(intent=intent, department=department).observe(steps)


def record_manager_failure(reason: str, intent: str, department: str):
    """Record manager failure"""
    MANAGER_FAILURE_REASONS.labels(reason=reason, intent=intent, department=department).inc()


def record_agent_execution(metrics: AgentExecutionMetrics):
    """Record agent execution metrics"""
    AGENT_TOKENS_TOTAL.labels(
        department=metrics.department, intent=metrics.intent, provider=metrics.provider
    ).inc(metrics.tokens)
    AGENT_COST_USD_TOTAL.labels(
        department=metrics.department, intent=metrics.intent, provider=metrics.provider
    ).inc(metrics.cost_usd)
    AGENT_LATENCY_MS.labels(
        department=metrics.department, intent=metrics.intent, provider=metrics.provider
    ).observe(metrics.latency_ms)
