from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.db import SessionLocal
from celery import shared_task


@shared_task(name="maintenance.cleanup_runs")
def cleanup_old_runs(days: int = 30) -> dict[str, Any]:
    """Delete old PersonalRun, InvestigationRun, and Artifact records older than N days."""

    from app.models import Artifact, InvestigationRun, PersonalRun
    cutoff = datetime.now(UTC) - timedelta(days=max(1, int(days)))
    db = SessionLocal()
    stats: dict[str, int] = {"personal": 0, "investigations": 0, "artifacts": 0}
    try:
        stats["personal"] = (
            db.query(PersonalRun)
            .filter(PersonalRun.created_at.isnot(None))
            .filter(PersonalRun.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        stats["investigations"] = (
            db.query(InvestigationRun)
            .filter(InvestigationRun.created_at.isnot(None))
            .filter(InvestigationRun.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        stats["artifacts"] = (
            db.query(Artifact)
            .filter(Artifact.created_at.isnot(None))
            .filter(Artifact.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return {"status": "ok", "deleted": stats, "cutoff": cutoff.isoformat()}
    except Exception:
        db.rollback()
        return {"status": "error", "deleted": stats, "cutoff": cutoff.isoformat()}
    finally:
        db.close()



