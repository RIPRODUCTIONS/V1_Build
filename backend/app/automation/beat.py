from __future__ import annotations

from celery.schedules import crontab

from app.automation.celery_app import celery
from app.core.config import get_settings

# Only configure autonomous mode if enabled
settings = get_settings()
if getattr(settings, 'AUTONOMOUS_MODE', False):
    celery.conf.beat_schedule = {
        'daily-autonomous-pipeline': {
            'task': 'automation.run_full_pipeline_autonomous',
            'schedule': crontab.from_string(getattr(settings, 'AUTONOMOUS_IDEA_CRON', '0 8 * * *')),
            'args': (getattr(settings, 'AUTONOMOUS_TOPIC', 'emerging+automation'),),
        }
    }
