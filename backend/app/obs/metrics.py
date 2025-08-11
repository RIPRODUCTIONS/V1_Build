from __future__ import annotations

import time
from typing import Callable

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUESTS = Counter(
    "life_requests_total",
    "Life route requests",
    ["route", "dag_id", "skill", "status"],
)

LATENCY = Histogram(
    "life_request_latency_seconds",
    "Life route request latency seconds",
    ["route", "dag_id", "skill", "status"],
    buckets=[0.02, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            raw_status = int(response.status_code) if response else 0
            # group by class for aggregation (e.g., 2xx/4xx/5xx)
            status = f"{raw_status // 100}xx" if raw_status else "0"
            # Prefer templated path to control cardinality
            try:
                route_obj = request.scope.get("route")
                route = getattr(route_obj, "path", request.url.path)
            except Exception:
                route = request.url.path
            # Skip self/health endpoints for recording
            if route not in ("/metrics", "/health", "/healthz", "/readyz"):
                dag_id = getattr(request.state, "dag_id", "unknown")
                skill = getattr(request.state, "skill", "unknown")
                dur = time.perf_counter() - start
                REQUESTS.labels(route, dag_id, skill, status).inc()
                LATENCY.labels(route, dag_id, skill, status).observe(dur)


def metrics_endpoint() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


