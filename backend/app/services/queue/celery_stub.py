"""Compatibility wrapper for Celery usage in new modules without touching existing wiring."""

from typing import Any


def enqueue(task_name: str, payload: dict[str, Any]) -> bool:
    # Integrate with existing Celery if/when needed; no-op for scaffold.
    return True
