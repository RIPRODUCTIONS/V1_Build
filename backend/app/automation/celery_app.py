# ruff: noqa: I001
from celery import Celery
from celery.signals import worker_process_init
from contextlib import suppress

from app.core.config import Settings
from app.ops.otel import init_tracing

s = Settings()
celery = Celery("automation", broker=s.CELERY_BROKER_URL, backend=s.CELERY_RESULT_BACKEND)
celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="automation",
)


@worker_process_init.connect
def _init_tracing(*args, **kwargs):  # noqa: ANN001
    with suppress(Exception):
        init_tracing("celery-worker")
