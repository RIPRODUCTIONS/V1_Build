from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter

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


