from __future__ import annotations

from datetime import UTC, datetime, timedelta

import boto3
from app.agent.celery_app import celery_app
from app.agent.pipeline import run_agent_pipeline
from app.core.config import get_settings
from app.db import SessionLocal
from app.models import Artifact, Task
from sqlalchemy import select
from sqlalchemy.orm import Session


@celery_app.task(
    bind=True,
    name="agent.run_pipeline",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_pipeline_task(
    self, owner_id: int, lead_id: int | None, context: str, run_id: int | None = None
) -> int:
    db: Session = SessionLocal()
    try:
        run = run_agent_pipeline(
            db, owner_id=owner_id, lead_id=lead_id, context=context, run_id=run_id
        )
        # schedule follow-up task in 24h
        create_followup_task.apply_async(
            args=[owner_id, lead_id or 0, "Send follow-up email"], countdown=24 * 60 * 60
        )
        return run.id
    except Exception as exc:
        raise self.retry(exc=exc) from None
    finally:
        db.close()


@celery_app.task(name="agent.create_followup_task")
def create_followup_task(owner_id: int, lead_id: int, title: str) -> int:
    db: Session = SessionLocal()
    try:
        t = Task(owner_id=owner_id, lead_id=lead_id, title=title, status="todo")
        db.add(t)
        db.commit()
        db.refresh(t)
        return t.id
    finally:
        db.close()


@celery_app.task(name="agent.cleanup_old_artifacts")
def cleanup_old_artifacts(days: int = 30) -> int:
    """Delete artifacts older than `days` days. Removes S3 objects if file_path is s3://.
    Returns number of artifacts deleted.
    """
    cutoff = datetime.now(UTC) - timedelta(days=days)
    settings = get_settings()
    s3 = None
    if settings.s3_endpoint_url and settings.s3_access_key and settings.s3_secret_key:
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    db: Session = SessionLocal()
    deleted = 0
    try:
        old_rows = db.scalars(
            select(Artifact).where(Artifact.created_at < cutoff, Artifact.status == "completed")
        ).all()
        for art in old_rows:
            # Try to delete S3 object
            if s3 and art.file_path and art.file_path.startswith("s3://"):
                try:
                    _, rest = art.file_path.split("s3://", 1)
                    bucket, key = rest.split("/", 1)
                    s3.delete_object(Bucket=bucket, Key=key)
                except Exception:
                    pass
            db.delete(art)
            deleted += 1
        db.commit()
        return deleted
    finally:
        db.close()


from typing import Any


@celery_app.task(name="system.autonomy.tick", autoretry_for=(Exception,), retry_backoff=True)
def system_autonomy_tick() -> dict[str, Any]:
    from datetime import datetime, timedelta

    from app.db import SessionLocal
    from app.models import SystemAutonomy
    from app.tasks.investigation_tasks import run_investigations_autopilot

    db: Session = SessionLocal()
    try:
        cfg = db.query(SystemAutonomy).first()
        if not cfg or not cfg.enabled:
            return {"status": "disabled"}
        now = datetime.now(timezone.utc)
        if cfg.last_tick and now - cfg.last_tick < timedelta(minutes=cfg.run_interval_minutes):
            return {"status": "skipped", "next_in_minutes": cfg.run_interval_minutes}
        res = run_investigations_autopilot.apply(args=[["task_data"], {"subject": {"name": "Jane Doe"}, "task_id": None}]) if False else run_investigations_autopilot.apply(args=[{"subject": {"name": "Jane Doe"}, "task_id": None}])
        cfg.last_tick = now
        cfg.last_error = None
        db.add(cfg)
        db.commit()
        data = res.result if hasattr(res, "result") else {}
        return {"status": "ok", "executed": True, "plan": data.get("plan"), "steps": [list(s.keys())[0] for s in data.get("steps", [])]}
    except Exception as e:
        try:
            cfg = db.query(SystemAutonomy).first()
            if cfg:
                cfg.last_error = str(e)
                db.add(cfg)
                db.commit()
        except Exception:
            pass
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
