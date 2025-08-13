from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Header

from app.integrations.hub import IntegrationHub
from app.integrations.google_workspace import (
    GoogleCalendarIntegration,
    GmailIntegration,
    GoogleDriveIntegration,
)


router = APIRouter(prefix="/assistant", tags=["assistant"])
hub = IntegrationHub()
hub.register("google_calendar", GoogleCalendarIntegration())
hub.register("gmail", GmailIntegration())
hub.register("google_drive", GoogleDriveIntegration())


def _now_iso(offset_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)).isoformat()


@router.post("/execute")
async def execute(intent: str, user_id: str = "1") -> Dict[str, Any]:
    """
    Natural-language assistant: routes to Google actions.

    Examples:
    - "draft email to rippyproduction@gmail.com about demo tomorrow"
    - "create document 'Plan' with text 'Kickoff at 9am'"
    - "add calendar event 'Standup' tomorrow 10:00-10:30 America/Chicago"
    """
    intent_lc = intent.lower()
    out: Dict[str, Any] = {"intent": intent, "results": []}

    # Heuristics (fast path). If OpenAI key is present we could enhance, but keep robust fallback.
    try:
        if any(k in intent_lc for k in ["calendar", "event", "meeting"]):
            title = _extract_between(intent, "'", "'") or _extract_after(intent, "event", default="New Event")
            start_iso, end_iso, tz = _coerce_time_window(intent)  # best-effort
            cal = hub.integrations.get("google_calendar")
            if isinstance(cal, GoogleCalendarIntegration):
                res = await cal.create_event(user_id, title, start_iso, end_iso, tz)
                out["results"].append({"action": "calendar.create", "response": res})

        if any(k in intent_lc for k in ["draft", "email"]):
            to = _extract_email(intent) or "rippyproduction@gmail.com"
            subj = _extract_after(intent, "about", default="Builder Draft")
            body = _extract_after(intent, "say", default="Hello from Builder.")
            gm = hub.integrations.get("gmail")
            if isinstance(gm, GmailIntegration):
                res = await gm.create_draft(user_id, to, subj, body)
                out["results"].append({"action": "gmail.draft", "response": res})

        if any(k in intent_lc for k in ["doc", "document", "text file", "note"]):
            drv = hub.integrations.get("google_drive")
            title = _extract_between(intent, "'", "'") or "Builder Doc"
            content = _extract_after(intent, "with", default="Created by Builder.")
            if isinstance(drv, GoogleDriveIntegration):
                # Choose doc vs text based on keyword
                if "text" in intent_lc:
                    res = await drv.create_text_file(user_id, f"{title}.txt", content)
                    out["results"].append({"action": "drive.create_text", "response": res})
                else:
                    res = await drv.create_document(user_id, title, content)
                    out["results"].append({"action": "drive.create_doc", "response": res})
    except Exception as e:
        out["error"] = str(e)
    return out


@router.post("/self_build/scan")
def self_build_scan(x_api_key: str | None = Header(default=None)) -> dict:
    _enforce_api_key(x_api_key)
    """Analyze recent runs and propose next templates automatically."""
    from app.db import SessionLocal
    from app.models import InvestigationRun, SystemInsight, AutoTemplateProposal
    from datetime import datetime, timedelta
    import json as _json
    from app.ai.system_brain import propose_new_templates

    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=7)
        runs = (
            db.query(InvestigationRun)
            .filter(InvestigationRun.created_at >= since)
            .order_by(InvestigationRun.created_at.desc())
            .all()
        )
        platform_counts: dict[str, int] = {}
        for r in runs:
            try:
                if r.result_summary_json:
                    s = _json.loads(r.result_summary_json)
                    # try dict form first
                    if isinstance(s.get("platforms"), dict):
                        for k in s["platforms"].keys():
                            platform_counts[k] = platform_counts.get(k, 0) + 1
                    elif isinstance(s.get("platforms"), list):
                        for k in s["platforms"]:
                            if isinstance(k, str):
                                platform_counts[k] = platform_counts.get(k, 0) + 1
            except Exception:
                continue
        proposals = propose_new_templates({"platform_counts": platform_counts})
        # Persist insights
        insight = SystemInsight(kind="investigation", title="Weekly self-build scan", details_json=_json.dumps({"platform_counts": platform_counts}))
        db.add(insight)
        for p in proposals:
            rec = AutoTemplateProposal(
                template_id=p.get("template_id"),
                name=p["name"],
                description=p.get("description"),
                category=p.get("category", "generated"),
                parameters_json=_json.dumps(p.get("parameters") or {}),
                score=float(p.get("score") or 0.0),
            )
            db.add(rec)
        db.commit()
        return {"status": "ok", "platform_counts": platform_counts, "proposals": proposals}
    finally:
        db.close()


@router.get("/self_build/proposals")
def list_self_build_proposals(limit: int = 50, x_api_key: str | None = Header(default=None)) -> dict:
    _enforce_api_key(x_api_key, read_only=True)
    from app.db import SessionLocal
    from app.models import AutoTemplateProposal
    db = SessionLocal()
    try:
        rows = (
            db.query(AutoTemplateProposal)
            .order_by(AutoTemplateProposal.created_at.desc())
            .limit(max(1, min(200, limit)))
            .all()
        )
        items = []
        for r in rows:
            items.append({
                "id": r.id,
                "template_id": r.template_id,
                "name": r.name,
                "description": r.description,
                "category": r.category,
                "score": r.score,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return {"items": items}
    finally:
        db.close()


@router.post("/self_build/proposals/{proposal_id}/approve")
def approve_self_build_proposal(proposal_id: int, x_api_key: str | None = Header(default=None)) -> dict:
    _enforce_api_key(x_api_key)
    from app.db import SessionLocal
    from app.models import AutoTemplateProposal
    db = SessionLocal()
    try:
        r = db.query(AutoTemplateProposal).filter(AutoTemplateProposal.id == proposal_id).first()
        if not r:
            return {"status": "not_found"}
        r.status = "approved"
        db.add(r)
        db.commit()
        return {"status": "ok", "id": r.id, "new_status": r.status}
    finally:
        db.close()


@router.post("/self_build/proposals/{proposal_id}/apply")
def apply_self_build_proposal(proposal_id: int, x_api_key: str | None = Header(default=None)) -> dict:
    _enforce_api_key(x_api_key)
    from app.db import SessionLocal
    from app.models import AutoTemplateProposal, AutomationTemplate
    import json as _json
    db = SessionLocal()
    try:
        r = db.query(AutoTemplateProposal).filter(AutoTemplateProposal.id == proposal_id).first()
        if not r:
            return {"status": "not_found"}
        # Create or update AutomationTemplate
        tpl = db.query(AutomationTemplate).filter(AutomationTemplate.id == (r.template_id or r.name.lower().replace(' ', '_'))).first()
        if not tpl:
            tpl_id = r.template_id or r.name.lower().replace(' ', '_')
            tpl = AutomationTemplate(
                id=tpl_id,
                name=r.name,
                description=r.description,
                category=r.category,
                template_config_json=_json.dumps({"generated": True}),
                required_parameters_json=r.parameters_json or _json.dumps({}),
            )
        else:
            tpl.name = r.name
            tpl.description = r.description
            tpl.category = r.category
        db.add(tpl)
        r.status = "applied"
        db.add(r)
        db.commit()
        return {"status": "ok", "template_id": tpl.id}
    finally:
        db.close()


def _enforce_api_key(x_api_key: str | None, read_only: bool = False) -> None:
    import os as _os
    if (_os.getenv("SECURE_MODE", "false").lower() == "true"):
        expected = _os.getenv("INTERNAL_API_KEY")
        if not expected or x_api_key != expected:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="unauthorized")

def _extract_between(text: str, start: str, end: str) -> str | None:
    try:
        i = text.index(start)
        j = text.index(end, i + 1)
        if j > i:
            return text[i + 1 : j].strip()
    except Exception:
        return None
    return None


def _extract_after(text: str, marker: str, default: str) -> str:
    i = text.lower().find(marker.lower())
    if i == -1:
        return default
    frag = text[i + len(marker) :].strip()
    return frag or default


def _extract_email(text: str) -> str | None:
    import re

    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else None


def _coerce_time_window(text: str) -> tuple[str, str, str | None]:
    tz = "America/Chicago"
    # naive: if "tomorrow" present, schedule 10:00-10:30 local; else +15min window
    if "tomorrow" in text.lower():
        d = datetime.now(timezone.utc) + timedelta(days=1)
        start = d.replace(hour=15, minute=0, second=0, microsecond=0)  # 10:00 -05:00 in UTC approx
        end = start + timedelta(minutes=30)
        return start.isoformat(), end.isoformat(), tz
    start = _now_iso(15)
    end = _now_iso(45)
    return start, end, tz


