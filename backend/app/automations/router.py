from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from app.automations.models import AutomationRule, RuleExecution
from app.db import get_db
from app.dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import case, func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/automations", tags=["automations"])


class RuleCreate(BaseModel):
    id: str
    name: str
    description: str | None = None
    trigger_type: str
    event_pattern: str | None = None
    conditions: dict = Field(default_factory=dict)
    actions: list[dict] = Field(default_factory=list)
    enabled: bool = True


@router.get("/rules")
def list_rules(
    user_id: Annotated[int, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    rows = db.query(AutomationRule).filter((AutomationRule.user_id == None) | (AutomationRule.user_id == str(user_id))).all()  # noqa: E711
    return rows


@router.get("/health")
def automation_health(db: Annotated[Session, Depends(get_db)]):
    """Basic health metrics for automation system."""
    try:
        import redis
        from app.core.config import get_settings

        settings = get_settings()
        r = redis.from_url(settings.REDIS_URL)
        try:
            info = r.xinfo_stream("automation-events")
            lag = info.get("length", 0)
        except Exception:
            lag = 0

        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        recent = db.query(RuleExecution).filter(RuleExecution.executed_at >= one_hour_ago).all()
        total = len(recent)
        failed = sum(1 for e in recent if e.status == "failed")
        error_rate = (failed / total * 100) if total else 0.0

        active_rules = db.query(AutomationRule).filter(AutomationRule.enabled.is_(True)).count()

        status = "healthy"
        if error_rate >= 10 or lag >= 1000:
            status = "degraded"
        return {
            "status": status,
            "metrics": {
                "stream_lag": lag,
                "recent_executions_1h": total,
                "error_rate_1h": round(error_rate, 2),
                "active_rules": active_rules,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:  # pragma: no cover
        return {"status": "error", "error": str(e)}


@router.get("/metrics")
def automation_metrics(db: Annotated[Session, Depends(get_db)]):
    since = datetime.now(UTC) - timedelta(hours=24)
    rows = (
        db.query(
            RuleExecution.rule_id,
            AutomationRule.name,
            func.count(RuleExecution.id).label("total"),
            func.sum(case((RuleExecution.status == "success", 1), else_=0)).label("success"),
            func.sum(case((RuleExecution.status == "failed", 1), else_=0)).label("failed"),
        )
        .join(AutomationRule, AutomationRule.id == RuleExecution.rule_id)
        .filter(RuleExecution.executed_at >= since)
        .group_by(RuleExecution.rule_id, AutomationRule.name)
        .all()
    )
    summary = {
        "total_executions": int(sum(r.total for r in rows)),
        "total_success": int(sum((r.success or 0) for r in rows)),
        "total_failed": int(sum((r.failed or 0) for r in rows)),
    }
    rules = [
        {
            "name": r.name,
            "executions": int(r.total),
            "success": int(r.success or 0),
            "failed": int(r.failed or 0),
            "success_rate": f"{((r.success or 0) / r.total * 100):.1f}%" if r.total else "0%",
        }
        for r in rows
    ]
    return {"period": "24h", "rules": rules, "summary": summary}


@router.post("/rules")
def create_rule(
    payload: RuleCreate,
    user_id: Annotated[int, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if db.get(AutomationRule, payload.id):
        raise HTTPException(status_code=400, detail="rule id already exists")
    row = AutomationRule(
        id=payload.id,
        user_id=str(user_id),
        name=payload.name,
        description=payload.description,
        trigger_type=payload.trigger_type,
        event_pattern=payload.event_pattern,
        conditions=payload.conditions,
        actions=payload.actions,
        enabled=payload.enabled,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/rules/{rule_id}/toggle")
def toggle_rule(
    rule_id: str,
    user_id: Annotated[int, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    row = db.get(AutomationRule, rule_id)
    if not row or (row.user_id not in (None, str(user_id))):
        raise HTTPException(status_code=404, detail="rule not found")
    row.enabled = not bool(row.enabled)  # type: ignore[assignment]
    db.commit()
    db.refresh(row)
    return {"id": row.id, "enabled": row.enabled}


@router.get("/executions")
def get_executions(
    user_id: Annotated[int, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    rows = (
        db.query(RuleExecution)
        .join(AutomationRule, AutomationRule.id == RuleExecution.rule_id)
        .filter((AutomationRule.user_id == None) | (AutomationRule.user_id == str(user_id)))  # noqa: E711
        .order_by(RuleExecution.executed_at.desc())
        .limit(100)
        .all()
    )
    return rows


