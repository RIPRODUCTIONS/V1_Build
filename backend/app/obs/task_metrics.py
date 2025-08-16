from __future__ import annotations

import contextlib
from datetime import UTC, datetime

from prometheus_client import Counter, Histogram

TASK_EVENTS = Counter(
    "builder_task_events_total",
    "Task lifecycle events",
    labelnames=("kind", "status"),
)

TASK_DURATION = Histogram(
    "builder_task_duration_seconds",
    "Task completion durations",
    labelnames=("kind",),
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600),
)


def record_started(kind: str) -> None:
    with contextlib.suppress(Exception):
        TASK_EVENTS.labels(kind=kind, status="started").inc()


def record_completed(kind: str, started_at: datetime | None) -> None:
    try:
        TASK_EVENTS.labels(kind=kind, status="completed").inc()
        if started_at is not None:
            if started_at.tzinfo is None:
                # Treat naive as UTC
                started_at = started_at.replace(tzinfo=UTC)
            dt = datetime.now(UTC) - started_at
            TASK_DURATION.labels(kind=kind).observe(max(0.0, dt.total_seconds()))
    except Exception:
        pass


def record_failed(kind: str, started_at: datetime | None) -> None:
    try:
        TASK_EVENTS.labels(kind=kind, status="failed").inc()
        if started_at is not None:
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=UTC)
            dt = datetime.now(UTC) - started_at
            TASK_DURATION.labels(kind=kind).observe(max(0.0, dt.total_seconds()))
    except Exception:
        pass



