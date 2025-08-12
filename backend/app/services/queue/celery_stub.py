from __future__ import annotations


class EventBus:
    """Simple in-memory stub for publishing domain events.

    Replace with Redis Streams or Kafka in real deployments.
    """

    def publish(self, topic: str, event: dict[str, object]) -> None:  # pragma: no cover
        print(f'[EVENT] topic={topic} event={event}')


"""Compatibility wrapper for Celery usage in new modules without touching existing wiring."""


def enqueue(task_name: str, payload: dict[str, object]) -> bool:
    # Integrate with existing Celery if/when needed; no-op for scaffold.
    return True
