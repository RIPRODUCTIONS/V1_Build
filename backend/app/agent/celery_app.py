from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("builder", broker=REDIS_URL, backend=REDIS_URL, include=[
    "app.agent.tasks",
    "app.integrations.tasks",
    "app.automations.tasks",
    "app.tasks.web_automation_tasks",
    "app.tasks.personal_automation_tasks",
])

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_routes={
        "app.agent.tasks.run_pipeline_task": {"queue": "agent"},
        "app.agent.tasks.create_followup_task": {"queue": "default"},
        "app.integrations.tasks.*": {"queue": "integrations"},
        "app.automations.tasks.*": {"queue": "automations"},
        "automation.execute_web_task": {"queue": "automations"},
        "personal.research.execute": {"queue": "automations"},
        "personal.shopping.execute": {"queue": "automations"},
        "personal.social.execute": {"queue": "automations"},
        "personal.email.execute": {"queue": "automations"},
        "personal.finance.execute": {"queue": "automations"},
    },
    beat_schedule={
        # Nightly housekeeping at 03:00 UTC: cleanup artifacts older than 30 days
        "cleanup_old_artifacts": {
            "task": "app.agent.tasks.cleanup_old_artifacts",
            "schedule": 24 * 60 * 60,  # daily
            "args": [30],
        },
        # Integration syncs: every 15 minutes
        "integrations_sync_all_users": {
            "task": "app.integrations.tasks.discover_new_integrations",
            "schedule": 15 * 60,
            "args": ["u1"],  # TODO: iterate real user ids
        },
        # Per-user full sync every 10 minutes (user_id "1")
        "integrations_sync_user_1": {
            "task": "app.integrations.tasks.sync_user_all",
            "schedule": 10 * 60,
            "args": ["1"],
        },
        # Token refresh every 30 minutes
        "integrations_refresh_tokens": {
            "task": "app.integrations.tasks.refresh_expiring_tokens",
            "schedule": 30 * 60,
        },
    },
)
