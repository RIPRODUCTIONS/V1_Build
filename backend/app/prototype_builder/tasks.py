import logging
import uuid

from celery import Celery

from .cursor_controller import drive_cursor_action

try:
    from app.agent.tasks import celery_app as _existing_celery_app  # reuse existing Celery app
except Exception:  # pragma: no cover - fallback stub
    _existing_celery_app = None

celery_app = _existing_celery_app or Celery(__name__, broker="memory://", backend="rpc://")

logger = logging.getLogger(__name__)


async def enqueue_build(name: str, prompt: str, repo_dir: str | None = None) -> str:
    run_id = str(uuid.uuid4())
    celery_app.send_task(
        "app.prototype_builder.tasks._build_task", args=[run_id, name, prompt, repo_dir]
    )
    return run_id


@celery_app.task(name="app.prototype_builder.tasks._build_task", acks_late=True)
def _build_task(run_id: str, name: str, prompt: str, repo_dir: str | None = None):
    logger.info("Prototype build started", extra={"run_id": run_id, "name": name})
    # Simulate doing some work via the cursor controller placeholder
    _ = drive_cursor_action("noop")
    # Write a tiny artifact file to /tmp using existing verification_engine
    from .verification_engine import verify

    ok_report = verify({"id": run_id})
    logger.info(
        "Prototype build finished", extra={"run_id": run_id, "ok": True, "report": ok_report}
    )
    return True
