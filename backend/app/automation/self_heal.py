from __future__ import annotations

import time
import traceback
from collections.abc import Callable
from typing import Any

from app.obs.metrics import (
    AI_FAILURES_TOTAL,
    AI_RETRY_LATENCY_SECONDS,
    AI_SELF_HEAL_ATTEMPTS_TOTAL,
)

FailureClass = str  # e.g. "VALIDATION","DEPENDENCY","RUNTIME","RATE_LIMIT"


def classify_failure(exc: Exception, tb: str) -> FailureClass:
    """Classify failure type for appropriate retry strategy."""
    msg = f'{type(exc).__name__}:{str(exc)} {tb}'.lower()
    if '429' in msg or 'rate' in msg:
        return 'RATE_LIMIT'
    if 'timeout' in msg or 'connection' in msg:
        return 'DEPENDENCY'
    if 'validation' in msg or 'schema' in msg:
        return 'VALIDATION'
    return 'RUNTIME'


def self_heal(task_name: str, fn: Callable[..., Any], max_retries=3, backoff=2.0):
    """Wrapper that provides self-healing with retries and failure classification."""

    def wrapped(*args, **kwargs):
        attempts, delay = 0, 1.0

        while True:
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception as e:
                tb = traceback.format_exc()
                fclass = classify_failure(e, tb)
                AI_FAILURES_TOTAL.labels(task=task_name, failure_class=fclass).inc()

                if attempts >= max_retries:
                    # Log final failure
                    print(f'Task {task_name} failed after {attempts} attempts: {e}')
                    raise

                attempts += 1
                AI_SELF_HEAL_ATTEMPTS_TOTAL.labels(task=task_name, failure_class=fclass).inc()

                start = time.time()
                # Adjust delay based on failure type
                if fclass == 'RATE_LIMIT':
                    delay = max(delay, backoff * attempts)
                elif fclass == 'DEPENDENCY':
                    delay = min(backoff * (attempts + 1), 15.0)

                print(
                    f'Task {task_name} failed (attempt {attempts}/{max_retries}), retrying in {delay:.1f}s...'
                )
                time.sleep(delay)

                AI_RETRY_LATENCY_SECONDS.labels(task=task_name, failure_class=fclass).observe(
                    time.time() - start
                )

                # Optional: tweak prompt/params in kwargs here based on fclass
                if fclass == 'RATE_LIMIT' and 'temperature' in kwargs:
                    kwargs['temperature'] = min(kwargs.get('temperature', 0.7) * 0.9, 0.3)

    return wrapped
