from __future__ import annotations

from typing import Any

from celery import shared_task


@shared_task(name="monitor.synthetic.osint", bind=True, autoretry_for=(Exception,), retry_backoff=True)
def synthetic_osint_smoke(self, task_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run a tiny OSINT plan end-to-end and assert artifacts exist. Creates a SystemInsight on failure."""
    import json as _json

    from app.db import SessionLocal
    from app.models import SystemInsight
    from app.tasks.investigation_tasks import run_osint_dossier

    subject = ((task_data or {}).get("subject") or {"name": "Smoke User"})
    res = run_osint_dossier.apply(args=[{"subject": subject, "task_id": None}]).result
    ok = bool(res.get("plan")) and (res.get("entities") is not None)
    if not ok:
        db = SessionLocal()
        try:
            insight = SystemInsight(
                kind="investigation",
                title="Synthetic OSINT smoke failed",
                details_json=_json.dumps({"result": res})
            )
            db.add(insight)
            db.commit()
        finally:
            db.close()
        return {"status": "error", "reason": "missing plan/entities"}
    return {"status": "ok"}


@shared_task(name="monitor.sse.watchdog", bind=True)
def sse_watchdog(self, max_age_seconds: int = 60) -> dict[str, Any]:
    """Detect investigations stuck in queued too long and create a SystemInsight."""
    import json as _json
    from datetime import datetime, timedelta, timezone

    from app.db import SessionLocal
    from app.models import InvestigationRun, SystemInsight

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=max_age_seconds)
    db = SessionLocal()
    try:
        stale = db.query(InvestigationRun).filter(InvestigationRun.status == "queued", InvestigationRun.created_at < cutoff).all()
        if not stale:
            return {"status": "ok", "stale": 0}
        insight = SystemInsight(
            kind="investigation",
            title="SSE/Run watchdog: stale queued runs",
            details_json=_json.dumps({"count": len(stale), "ids": [r.id for r in stale]})
        )
        db.add(insight)
        db.commit()
        return {"status": "alert", "stale": len(stale)}
    finally:
        db.close()



