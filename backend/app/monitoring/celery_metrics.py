from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

from celery.signals import task_failure, task_postrun, task_prerun, task_success
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


# Prometheus metrics for Celery tasks
celery_task_duration = Histogram(
    "celery_task_duration_seconds",
    "Time spent processing Celery tasks",
    ["task_name", "queue", "status"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

celery_task_total = Counter(
    "celery_task_total",
    "Total number of Celery tasks",
    ["task_name", "queue", "status"],
)

celery_queue_depth = Gauge(
    "celery_queue_depth",
    "Number of tasks waiting in queue",
    ["queue"],
)

celery_active_tasks = Gauge(
    "celery_active_tasks",
    "Number of currently active tasks",
    ["task_name"],
)


# Task timing storage
task_start_times: dict[str, float] = {}


@task_prerun.connect
def task_prerun_handler(task_id: str, task: Any, *args, **kwargs):
    """Record task start time and increment active tasks."""
    try:
        task_start_times[task_id] = time.time()
        celery_active_tasks.labels(task_name=task.name).inc()
        logger.info("Starting task %s with ID %s", task.name, task_id)
    except Exception:
        pass


@task_postrun.connect
def task_postrun_handler(task_id: str, task: Any, *args, **kwargs):
    """Record task completion time and metrics."""
    try:
        started = task_start_times.pop(task_id, None)
        if started is not None:
            duration = max(0.0, time.time() - started)
            celery_task_duration.labels(
                task_name=task.name,
                queue=getattr(task, "queue", "default"),
                status="completed",
            ).observe(duration)
        celery_active_tasks.labels(task_name=task.name).dec()
        logger.info("Completed task %s with ID %s", task.name, task_id)
    except Exception:
        pass


@task_success.connect
def task_success_handler(result: Any, **kwargs):
    """Record successful task completion."""
    try:
        task = kwargs.get("sender")
        if task:
            celery_task_total.labels(
                task_name=task.name,
                queue=getattr(task, "queue", "default"),
                status="success",
            ).inc()
    except Exception:
        pass


@task_failure.connect
def task_failure_handler(task_id: str, exception: Exception, einfo: Any, **kwargs):
    """Record task failures and log."""
    try:
        task = kwargs.get("sender")
        if task:
            celery_task_total.labels(
                task_name=task.name,
                queue=getattr(task, "queue", "default"),
                status="failure",
            ).inc()
            logger.error("Task %s failed: %s", task.name, exception)
    except Exception:
        pass


# Periodic queue depth updater (best-effort)
try:
    from app.agent.celery_app import celery_app
    from celery import shared_task

    @celery_app.on_after_finalize.connect
    def _setup_monitoring_periodic(sender, **kwargs):
        try:
            sender.add_periodic_task(60.0, update_queue_metrics.s(), name="monitor.update_queue_metrics")
        except Exception:
            pass

    @shared_task(name="monitor.update_queue_metrics")
    def update_queue_metrics() -> None:
        """Update queue depth metrics using Redis LLEN for celery queues."""
        try:
            import redis  # lazy import to avoid test env issues
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
            r = redis.from_url(redis_url)
            try:
                # Default Celery queues we use
                queue_names = [
                    os.getenv("CELERY_DEFAULT_QUEUE", "default"),
                    "automations",
                    "integrations",
                    "webexec",
                    "agent",
                ]
                for qname in queue_names:
                    # Celery Redis transport queue key format
                    # https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html
                    key = f"celery\x06\x16q\x06\x16{qname}"
                    try:
                        depth = int(r.llen(key))
                        celery_queue_depth.labels(queue=qname).set(depth)
                    except Exception:
                        # Fall back to 0 on per-queue error
                        celery_queue_depth.labels(queue=qname).set(0)
            finally:
                try:
                    r.close()
                except Exception:
                    pass
        except Exception as exc:
            logger.debug("update_queue_metrics failed: %s", exc)

    # Expose a Prometheus HTTP endpoint from the worker so Prometheus can scrape Celery metrics
    from prometheus_client import start_http_server
    if os.getenv("ENABLE_CELERY_METRICS_HTTP", "true").lower() == "true":
        try:
            port = int(os.getenv("CELERY_METRICS_PORT", "9095"))
            threading.Thread(target=start_http_server, args=(port,), daemon=True).start()
            logger.info("Started Celery metrics HTTP server on port %d", port)
        except Exception as exc:
            logger.debug("failed to start metrics HTTP server: %s", exc)
except Exception:
    # Celery not initialized in some contexts (e.g., pure unit tests)
    pass


