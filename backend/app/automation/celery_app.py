# ruff: noqa: I001
from celery import Celery
from app.core.config import Settings

s = Settings()
celery = Celery("automation", broker=s.CELERY_BROKER_URL, backend=s.CELERY_RESULT_BACKEND)
celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="automation",
)
