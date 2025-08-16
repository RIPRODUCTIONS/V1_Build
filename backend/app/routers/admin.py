from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
import os
from typing import Annotated

from app.core.config import get_settings
from app.db import get_db
from app.models import AgentRun, Artifact, Lead, Task
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import delete
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import time

router = APIRouter(prefix="/admin", tags=["admin"])
_logger = logging.getLogger("cleanup")

# Simple in-memory rate limiter: IP -> deque[timestamps]
_RATE_WINDOW_SECONDS = 60
_RATE_MAX_REQUESTS = 5
_ip_to_hits: dict[str, deque[float]] = defaultdict(deque)


def _get_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def require_rate_limit(request: Request) -> None:
    now = time.monotonic()
    ip = _get_ip(request)
    hits = _ip_to_hits[ip]
    # prune old entries
    while hits and now - hits[0] > _RATE_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= _RATE_MAX_REQUESTS:
        _logger.info(
            "cleanup_request",
            extra={
                "ts": datetime.now(timezone.utc).isoformat(),
                "ip": ip,
                "route": str(request.url.path),
                "auth": "rate_limited",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )
    hits.append(now)


def require_ci(
    request: Request, x_ci_token: Annotated[str | None, Header(alias="X-CI-Token")] = None
) -> None:
    settings = get_settings()
    ip = _get_ip(request)
    if not settings.ci_env:
        _logger.info(
            "cleanup_request",
            extra={
                "ts": datetime.now(timezone.utc).isoformat(),
                "ip": ip,
                "route": str(request.url.path),
                "auth": "ci_env_false",
            },
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin cleanup disabled")
    if not settings.ci_cleanup_token or x_ci_token != settings.ci_cleanup_token:
        _logger.info(
            "cleanup_request",
            extra={
                "ts": datetime.now(timezone.utc).isoformat(),
                "ip": ip,
                "route": str(request.url.path),
                "auth": "invalid_token",
            },
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    _logger.info(
        "cleanup_request",
        extra={
                "ts": datetime.now(timezone.utc).isoformat(),
            "ip": ip,
            "route": str(request.url.path),
            "auth": "success",
        },
    )


@router.delete("/cleanup/leads", status_code=204)
def cleanup_leads(
    _: Annotated[None, Depends(require_ci)],
    __: Annotated[None, Depends(require_rate_limit)],
    db: Annotated[Session, Depends(get_db)],
):
    db.execute(delete(Lead))
    db.commit()


# --- Integration admin visibility (no secrets) ---
from app.integrations.hub import IntegrationHub
from app.models import AutomationTemplate, TemplateUsage


@router.get("/integrations/status")
def integrations_status(_: Annotated[None, Depends(require_ci)]):
    hub = IntegrationHub()
    # Do not include secrets, only names and availability
    status = []
    for name in sorted(hub.integrations.keys()):
        status.append({"name": name})
    return {"integrations": status}


@router.get("/integrations/health")
def integrations_health(_: Annotated[None, Depends(require_ci)]):
    hub = IntegrationHub()
    health = []
    for name in sorted(hub.integrations.keys()):
        health.append(
            {
                "name": name,
                "last_sync": hub.last_sync.get(name),
                "error_rate": hub.error_rate.get(name, 0.0),
            }
        )
    return {"health": health}


@router.delete("/cleanup/tasks", status_code=204)
def cleanup_tasks(
    _: Annotated[None, Depends(require_ci)],
    __: Annotated[None, Depends(require_rate_limit)],
    db: Annotated[Session, Depends(get_db)],
):
    db.execute(delete(Task))
    db.commit()


# Dev-only task listing without JWT (guarded by CI token)
@router.get("/tasks", response_model=None)
def list_tasks_admin(
    _: Annotated[None, Depends(require_ci)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
):
    return db.query(Task).order_by(Task.created_at.desc()).limit(limit).all()


@router.delete("/cleanup/all", status_code=204)
def cleanup_all(
    _: Annotated[None, Depends(require_ci)],
    __: Annotated[None, Depends(require_rate_limit)],
    db: Annotated[Session, Depends(get_db)],
):
    # Order matters due to FKs
    db.execute(delete(Artifact))
    db.execute(delete(AgentRun))
    db.execute(delete(Task))
    db.execute(delete(Lead))
    # Users can also be removed if desired; keep default to retain admin user
    db.commit()


class GoogleOAuthIn(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = 3600


@router.post("/integrations/google/oauth/{user_id}")
def upsert_google_oauth(
    user_id: str,
    payload: GoogleOAuthIn,
    _: Annotated[None, Depends(require_ci)],
):
    from app.integrations.security import CredentialVault

    expires_at = int(time.time()) + int(payload.expires_in or 3600)
    rec = {
        "access_token": payload.access_token,
        "refresh_token": payload.refresh_token,
        "expires_at": expires_at,
    }
    v = CredentialVault.from_env()
    v.put(user_id, "google_calendar", "oauth", json.dumps(rec))
    return {"status": "ok", "user_id": user_id, "expires_at": expires_at}

@router.post("/automations/seed_calendar_rules")
def seed_calendar_rules(
    _: Annotated[None, Depends(require_ci)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.automations.models import AutomationRule
    rules = [
        AutomationRule(
            id="calendar_meeting_prep",
            user_id="system",
            name="Meeting Prep Task",
            description="Create prep task when calendar title contains 'meeting'",
            trigger_type="calendar.event.created",
            event_pattern="calendar.event.created",
            conditions={"title_contains": "meeting"},
            actions=[{"type": "create_task", "params": {"title": "Prep for meeting"}}],
            enabled=True,
        ),
        AutomationRule(
            id="calendar_attendee_notify",
            user_id="system",
            name="Attendee Notify",
            description="Notify when event includes user as attendee",
            trigger_type="calendar.event.created",
            event_pattern="calendar.event.created",
            conditions={"attendee_includes": "rippyproduction@gmail.com"},
            actions=[{"type": "send_notification", "params": {"channel": "email", "subject": "Calendar", "message": "You are on an event"}}],
            enabled=True,
        ),
    ]
    created = []
    for r in rules:
        if not db.get(AutomationRule, r.id):
            db.add(r)
            created.append(r.id)
    db.commit()
    return {"created": created}


# --- DLQ admin ---
from app.core.dlq import DeadLetterQueue
from app.core.event_bus import STREAM_KEY as SYSTEM_STREAM
from app.core.config import get_settings


@router.get("/dlq/{queue}/items")
def dlq_items(queue: str, limit: int = 50, _: Annotated[None, Depends(require_ci)] = None):
    dlq = DeadLetterQueue()
    return __import__("asyncio").run(dlq.get_dlq_items(queue, limit))


@router.post("/dlq/{queue}/replay/{item_id}")
def dlq_replay(queue: str, item_id: str, _: Annotated[None, Depends(require_ci)] = None):
    dlq = DeadLetterQueue()

    async def _replay(payload: dict) -> bool:
        # Simple echo replay hook; extend per-queue (e.g., re-enqueue to Celery task)
        return True

    ok = __import__("asyncio").run(dlq.replay_dlq_item(queue, item_id, _replay))
    return {"replayed": bool(ok)}


@router.get("/events/system/status")
def system_event_status(_: Annotated[None, Depends(require_ci)] = None):
    import redis

    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL)
    try:
        size = r.xlen(SYSTEM_STREAM)
        pending = r.xpending_range(SYSTEM_STREAM, get_settings().EVENT_BUS_CONSUMER_GROUP, min="-", max="+", count=1)
        return {"stream": SYSTEM_STREAM, "size": int(size), "has_pending": bool(list(pending))}
    finally:
        r.close()


@router.get("/events/system/dlq")
def system_event_dlq(_: Annotated[None, Depends(require_ci)] = None, limit: int = 20):
    import redis
    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL)
    try:
        lst = r.lrange(os.getenv("SYSTEM_EVENT_DLQ", "dlq:system_events"), 0, limit - 1)
        return {"items": [json.loads(x) for x in lst]}
    finally:
        r.close()


@router.get("/events/system/pending")
def system_event_pending(_: Annotated[None, Depends(require_ci)] = None):
    import redis
    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL)
    try:
        summary = r.xpending(SYSTEM_STREAM, settings.EVENT_BUS_CONSUMER_GROUP)
        # summary: (count, min, max, consumers)
        count, min_id, max_id, consumers = summary
        return {
            "stream": SYSTEM_STREAM,
            "group": settings.EVENT_BUS_CONSUMER_GROUP,
            "count": int(count),
            "min": min_id,
            "max": max_id,
            "consumers": [{"name": c[0], "pending": int(c[1])} for c in consumers],
        }
    finally:
        r.close()


class DlqReplayIn(BaseModel):
    count: int | None = 1


@router.post("/events/system/dlq/replay")
def system_event_dlq_replay(payload: DlqReplayIn, _: Annotated[None, Depends(require_ci)] = None):
    import redis
    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL)
    try:
        key = os.getenv("SYSTEM_EVENT_DLQ", "dlq:system_events")
        replayed: int = 0
        count_int: int = max(1, int(payload.count or 1))
        for __i in range(count_int):
            raw = r.rpop(key)
            if not raw:
                break
            item = json.loads(raw)
            fields = item.get("fields", {})
            # Re-publish to stream preserving original fields
            r.xadd(item.get("stream", SYSTEM_STREAM), fields)
            replayed += 1
        return {"replayed": replayed}
    finally:
        r.close()


class BulkReplayRequest(BaseModel):
    item_ids: list[str]
    user_id: str = "system"


@router.post("/dlq/{queue}/bulk_replay")
def dlq_bulk_replay(queue: str, request: BulkReplayRequest, _: Annotated[None, Depends(require_ci)] = None):
    dlq = DeadLetterQueue()

    async def _replay(payload: dict) -> bool:
        return True

    res = __import__("asyncio").run(dlq.bulk_replay_dlq_items(queue, request.item_ids, request.user_id, _replay))
    return res


# --- Template admin ---

class TemplateIn(BaseModel):
    id: str
    name: str
    description: str | None = None
    category: str
    difficulty: str | None = None
    estimated_time_minutes: int | None = None
    price_per_run_usd: float | None = None


@router.get("/templates")
def admin_list_templates(_: Annotated[None, Depends(require_ci)] = None):
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        rows = db.query(AutomationTemplate).order_by(AutomationTemplate.name.asc()).all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "category": r.category,
                "difficulty": r.difficulty,
                "estimated_time_minutes": r.estimated_time_minutes,
                "price_per_run_usd": r.price_per_run_usd,
            }
            for r in rows
        ]
    finally:
        db.close()


@router.post("/templates")
def admin_upsert_template(payload: TemplateIn, _: Annotated[None, Depends(require_ci)] = None):
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        rec = db.get(AutomationTemplate, payload.id)
        if not rec:
            rec = AutomationTemplate(id=payload.id, name=payload.name, category=payload.category)
            db.add(rec)
        rec.name = payload.name
        rec.description = payload.description
        rec.category = payload.category
        rec.difficulty = payload.difficulty
        rec.estimated_time_minutes = payload.estimated_time_minutes
        rec.price_per_run_usd = payload.price_per_run_usd
        db.commit()
        return {"status": "ok", "id": rec.id}
    finally:
        db.close()


@router.delete("/templates/{template_id}")
def admin_delete_template(template_id: str, _: Annotated[None, Depends(require_ci)] = None):
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        rec = db.get(AutomationTemplate, template_id)
        if rec:
            db.delete(rec)
            db.commit()
        return {"deleted": bool(rec)}
    finally:
        db.close()


@router.get("/templates/roi")
def admin_templates_roi(_: Annotated[None, Depends(require_ci)] = None):
    from app.db import SessionLocal
    from app.core.config import get_settings

    s = get_settings()
    db = SessionLocal()
    try:
        rows = (
            db.query(AutomationTemplate)
            .order_by(AutomationTemplate.name.asc())
            .all()
        )
        out = []
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None)  # naive to match DB default
        from datetime import timedelta
        cutoff = cutoff - timedelta(hours=24)
        for r in rows:
            # Approximate: time saved = usage_count * estimated_time_minutes
            usage_count = (
                db.query(TemplateUsage)
                .filter(TemplateUsage.template_id == r.id)
                .count()
            )
            last_24h_total = (
                db.query(TemplateUsage)
                .filter(TemplateUsage.template_id == r.id, TemplateUsage.created_at >= cutoff)
                .count()
            )
            last_24h_success = (
                db.query(TemplateUsage)
                .filter(
                    TemplateUsage.template_id == r.id,
                    TemplateUsage.created_at >= cutoff,
                    TemplateUsage.success.is_(True),
                )
                .count()
            )
            last_24h_failed = max(0, last_24h_total - last_24h_success)
            last_24h_success_rate = (last_24h_success / last_24h_total) if last_24h_total else 0.0
            minutes = (r.estimated_time_minutes or 3) * usage_count
            hours = minutes / 60.0
            savings = round(hours * float(s.ROI_HOURLY_RATE_USD), 2)
            out.append({
                "id": r.id,
                "name": r.name,
                "usage": usage_count,
                "estimated_time_saved_hours": round(hours, 2),
                "estimated_cost_savings_usd": savings,
                "last_24h": {
                    "runs": last_24h_total,
                    "success": last_24h_success,
                    "failed": last_24h_failed,
                    "success_rate": round(last_24h_success_rate, 3),
                },
            })
        return {"roi": out, "hourly_rate": s.ROI_HOURLY_RATE_USD}
    finally:
        db.close()


@router.get("/dlq/{queue}/items/{item_id}")
def dlq_item_details(queue: str, item_id: str, _: Annotated[None, Depends(require_ci)] = None):
    dlq = DeadLetterQueue()
    item = __import__("asyncio").run(dlq.get_dlq_item(queue, item_id))
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    return item
