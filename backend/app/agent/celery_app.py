from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

celery_app = Celery('builder', broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue='default',
    task_routes={
        'agent.run_pipeline': {'queue': 'agent'},
        'agent.create_followup_task': {'queue': 'default'},
    },
    beat_schedule={
        # Nightly housekeeping at 03:00 UTC: cleanup artifacts older than 30 days
        'cleanup_old_artifacts': {
            'task': 'agent.cleanup_old_artifacts',
            'schedule': 24 * 60 * 60,  # daily
            'args': [30],
        },
    },
)
