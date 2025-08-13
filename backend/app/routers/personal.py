from __future__ import annotations

from typing import Any, Dict, Annotated

from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db, SessionLocal
from app.tasks.personal_automation_tasks import (
    execute_personal_research,
    execute_personal_shopping,
    execute_personal_social,
    execute_personal_email,
    execute_personal_finance,
)
from app.agent.celery_app import celery_app
from celery.result import AsyncResult
from app.personal.personal_config import get_personal_config
import asyncio
import json
import os
import secrets
import urllib.parse as _url


router = APIRouter(prefix="/personal", tags=["personal"])


@router.post("/run/{template_id}")
def run_personal(template_id: str, payload: Dict[str, Any], db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    if template_id == "research_assistant":
        job = execute_personal_research.delay(payload)
        _record_personal_run(template_id, job.id, payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "shopping_assistant":
        job = execute_personal_shopping.delay(payload)
        _record_personal_run(template_id, job.id, payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "social_media_manager":
        job = execute_personal_social.delay(payload)
        _record_personal_run(template_id, job.id, payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "personal_email_manager":
        job = execute_personal_email.delay(payload)
        _record_personal_run(template_id, job.id, payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "personal_finance_tracker":
        job = execute_personal_finance.delay(payload)
        _record_personal_run(template_id, job.id, payload)
        return {"status": "queued", "task_id": job.id}
    return {"status": "unsupported", "template_id": template_id}


@router.get("/result/{task_id}")
def get_result(task_id: str) -> Dict[str, Any]:
    result: AsyncResult = celery_app.AsyncResult(task_id)
    state = result.state
    response: Dict[str, Any] = {"task_id": task_id, "state": state}
    if state == "SUCCESS":
        try:
            _res = result.get(timeout=0)
            response["result"] = _res
            _update_personal_run(task_id, "completed", _res)
            response["status"] = "completed"
        except Exception as exc:  # pragma: no cover - best effort
            response["status"] = "error"
            response["error"] = str(exc)
            _update_personal_run(task_id, "error", {"error": str(exc)})
    elif state in {"FAILURE", "REVOKED"}:
        response["status"] = "error"
        try:
            _err = str(result.result)
            response["error"] = _err
            _update_personal_run(task_id, "error", {"error": _err})
        except Exception:  # pragma: no cover
            pass
    else:
        response["status"] = "pending"
    return response


@router.get("/config")
def get_personal_integration_config() -> Dict[str, Any]:
    cfg = get_personal_config()
    return {
        "twitter_enabled": bool(cfg.twitter_enabled),
        "linkedin_enabled": bool(cfg.linkedin_enabled),
        "post_real_enabled": bool(cfg.post_real_enabled),
        "oauth": {
            "twitter": bool(cfg.twitter_client_id and cfg.twitter_redirect_uri),
            "linkedin": bool(cfg.linkedin_client_id and cfg.linkedin_redirect_uri),
        },
    }


@router.get("/stream/{task_id}")
async def stream_personal_task(task_id: str, request: Request) -> StreamingResponse:
    async def event_generator():
        last_state: str | None = None
        while True:
            if await request.is_disconnected():
                break
            result: AsyncResult = celery_app.AsyncResult(task_id)
            state = result.state
            payload: Dict[str, Any] = {"task_id": task_id, "state": state}
            status = "pending"
            if state == "SUCCESS":
                try:
                    _res = result.get(timeout=0)
                    payload["result"] = _res
                    _update_personal_run(task_id, "completed", _res)
                except Exception as exc:  # pragma: no cover
                    payload["error"] = str(exc)
                status = "completed"
            elif state in {"FAILURE", "REVOKED"}:
                try:
                    payload["error"] = str(result.result)
                except Exception:  # pragma: no cover
                    pass
                status = "error"
                _update_personal_run(task_id, "error", {"error": payload.get("error")})
            payload["status"] = status
            if state != last_state or status in {"completed", "error"}:
                yield f"data: {json.dumps(payload)}\n\n"
                last_state = state
            if status in {"completed", "error"}:
                break
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/runs")
def list_personal_runs(limit: int = 20) -> Dict[str, Any]:
    from app.models import PersonalRun

    db = SessionLocal()
    try:
        rows = (
            db.query(PersonalRun)
            .order_by(PersonalRun.created_at.desc())
            .limit(max(1, min(100, limit)))
            .all()
        )
        items = [
            {
                "id": r.id,
                "template_id": r.template_id,
                "task_id": r.task_id,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
        return {"items": items}
    finally:
        db.close()


def _record_personal_run(template_id: str, task_id: str, params: Dict[str, Any]) -> None:
    from app.models import PersonalRun
    import json as _json

    db = SessionLocal()
    try:
        rec = PersonalRun(
            template_id=template_id,
            task_id=task_id,
            status="queued",
            parameters_json=_json.dumps(params) if params else None,
        )
        db.add(rec)
        db.commit()
    finally:
        db.close()


def _update_personal_run(task_id: str, status: str, result_obj: Dict[str, Any] | None) -> None:
    from app.models import PersonalRun
    import json as _json
    from datetime import datetime as _dt

    db = SessionLocal()
    try:
        rec = db.query(PersonalRun).filter(PersonalRun.task_id == task_id).first()
        if rec:
            rec.status = status
            rec.result_summary_json = _json.dumps(result_obj or {})
            rec.updated_at = _dt.utcnow()
            db.add(rec)
            db.commit()
    finally:
        db.close()


@router.post("/finance/import_csv")
async def import_finance_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    import csv
    from io import StringIO

    raw = await file.read()
    try:
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        text = raw.decode("latin-1", errors="ignore")
    reader = csv.DictReader(StringIO(text))
    transactions = []
    total_spent = 0.0
    per_category: Dict[str, float] = {}
    def _cat(row: Dict[str, Any]) -> str:
        d = (row.get("description") or row.get("merchant") or "").lower()
        if any(k in d for k in ["uber", "lyft", "gas", "shell", "chevron"]):
            return "transport"
        if any(k in d for k in ["grocery", "market", "whole foods", "trader joe", "food"]):
            return "food"
        if any(k in d for k in ["netflix", "spotify", "prime", "subscription"]):
            return "entertainment"
        if any(k in d for k in ["walmart", "target", "amazon", "shop"]):
            return "shopping"
        return "other"
    for row in reader:
        try:
            amt_str = (row.get("amount") or row.get("Amount") or "0").replace(",", "").strip()
            amount = float(amt_str)
        except Exception:
            amount = 0.0
        cat = _cat(row)
        per_category[cat] = round(per_category.get(cat, 0.0) + amount, 2)
        total_spent = round(total_spent + amount, 2)
        transactions.append({
            "date": row.get("date") or row.get("Date"),
            "description": row.get("description") or row.get("Description") or row.get("merchant"),
            "amount": amount,
            "category": cat,
        })
        if len(transactions) >= 500:
            break
    return {
        "status": "ok",
        "parsed": len(transactions),
        "total_spent": total_spent,
        "per_category": per_category,
        "sample": transactions[:10],
    }


@router.post("/social/oauth/store/{provider}")
def store_social_oauth(provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from app.models import SocialAuth
    from app.db import SessionLocal
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        rec = SocialAuth(
            user_id=int(payload.get("user_id") or 1),  # placeholder single-user setup
            provider=provider,
            access_token=str(payload.get("access_token") or ""),
            refresh_token=payload.get("refresh_token"),
            expires_at=None,
        )
        if payload.get("expires_in"):
            try:
                _ = int(payload["expires_in"])  # seconds
                rec.expires_at = datetime.now(timezone.utc).replace(tzinfo=None)
            except Exception:
                pass
        db.add(rec)
        db.commit()
        return {"status": "ok", "id": rec.id}
    finally:
        db.close()


@router.delete("/social/oauth/{provider}")
def disconnect_social_oauth(provider: str, user_id: int | None = None) -> Dict[str, Any]:
    from app.models import SocialAuth
    db = SessionLocal()
    try:
        q = db.query(SocialAuth).filter(SocialAuth.provider == provider)
        if user_id:
            q = q.filter(SocialAuth.user_id == user_id)
        deleted = q.delete()
        db.commit()
        return {"status": "ok", "deleted": deleted}
    finally:
        db.close()


@router.get("/social/oauth/status")
def oauth_status(user_id: int | None = None) -> Dict[str, Any]:
    from app.models import SocialAuth
    db = SessionLocal()
    try:
        q = db.query(SocialAuth)
        if user_id:
            q = q.filter(SocialAuth.user_id == user_id)
        twitter = q.filter(SocialAuth.provider == "twitter").count() > 0
        linkedin = q.filter(SocialAuth.provider == "linkedin").count() > 0
        return {"twitter": twitter, "linkedin": linkedin}
    finally:
        db.close()


@router.get("/social/oauth/twitter/start")
def twitter_oauth_start() -> Dict[str, Any]:
    cfg = get_personal_config()
    if not (cfg.twitter_client_id and cfg.twitter_redirect_uri):
        return {"status": "disabled"}
    state = secrets.token_urlsafe(16)
    # Twitter v2 OAuth2 authorize URL (PKCE omitted for brevity)
    base = "https://twitter.com/i/oauth2/authorize"
    qs = {
        "response_type": "code",
        "client_id": cfg.twitter_client_id,
        "redirect_uri": cfg.twitter_redirect_uri,
        "scope": "tweet.read tweet.write users.read offline.access",
        "state": state,
        "code_challenge": state,
        "code_challenge_method": "plain",
    }
    url = f"{base}?{_url.urlencode(qs)}"
    return {"authorize_url": url, "state": state}


@router.get("/social/oauth/twitter/callback")
def twitter_oauth_callback(code: str | None = None, state: str | None = None) -> Dict[str, Any]:
    cfg = get_personal_config()
    if not code:
        return {"status": "error", "detail": "missing code"}
    if not cfg.oauth_exchange_real:
        return store_social_oauth("twitter", {"access_token": code})
    # Real exchange placeholder (without network access in tests):
    # In production, exchange 'code' for tokens via Twitter OAuth2 token endpoint
    return store_social_oauth("twitter", {"access_token": f"tw_{code}"})


@router.get("/social/oauth/linkedin/start")
def linkedin_oauth_start() -> Dict[str, Any]:
    cfg = get_personal_config()
    if not (cfg.linkedin_client_id and cfg.linkedin_redirect_uri):
        return {"status": "disabled"}
    state = secrets.token_urlsafe(16)
    base = "https://www.linkedin.com/oauth/v2/authorization"
    qs = {
        "response_type": "code",
        "client_id": cfg.linkedin_client_id,
        "redirect_uri": cfg.linkedin_redirect_uri,
        "state": state,
        "scope": "w_member_social r_liteprofile",
    }
    url = f"{base}?{_url.urlencode(qs)}"
    return {"authorize_url": url, "state": state}


@router.get("/social/oauth/linkedin/callback")
def linkedin_oauth_callback(code: str | None = None, state: str | None = None) -> Dict[str, Any]:
    cfg = get_personal_config()
    if not code:
        return {"status": "error", "detail": "missing code"}
    if not cfg.oauth_exchange_real:
        return store_social_oauth("linkedin", {"access_token": code})
    # Real exchange placeholder (without network access in tests):
    # In production, exchange 'code' for tokens via LinkedIn OAuth2 token endpoint
    return store_social_oauth("linkedin", {"access_token": f"li_{code}"})

