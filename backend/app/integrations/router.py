from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

import os
from .hub import IntegrationHub


router = APIRouter(prefix="/integrations", tags=["integrations"])
hub = IntegrationHub()

# Register mock provider by default (skip Google unless explicitly enabled)
try:
    from .mock_provider import MockCalendarIntegration

    hub.register("mock_calendar", MockCalendarIntegration())
except Exception:
    pass

if os.getenv("ENABLE_GOOGLE_INTEGRATIONS", "false").lower() in {"1", "true", "yes"}:
    try:
        from .google_workspace import (
            GoogleCalendarIntegration,
            GmailIntegration,
            GoogleDriveIntegration,
            GooglePeopleIntegration,
        )
        from .google_maps import GoogleMapsIntegration

        hub.register("google_calendar", GoogleCalendarIntegration())
        hub.register("gmail", GmailIntegration())
        hub.register("google_drive", GoogleDriveIntegration())
        hub.register("google_people", GooglePeopleIntegration())
        hub.register("google_maps", GoogleMapsIntegration())
    except Exception:
        # Silently skip if Google libs not available; we operate with mocks only
        pass


@router.get("/discover/{user_id}")
async def discover(user_id: str):
    found = await hub.auto_discover(user_id)
    return {"user_id": user_id, "integrations": found}


@router.post("/sync/{user_id}")
async def sync_all(user_id: str):
    results = await hub.sync_all(user_id)
    return {"user_id": user_id, "results": results}


@router.post("/google/calendar/test_event/{user_id}")
async def create_test_event(user_id: str):
    now = datetime.now(timezone.utc)
    start = (now + timedelta(minutes=5)).isoformat()
    end = (now + timedelta(minutes=35)).isoformat()
    integ = hub.integrations.get("google_calendar")
    if not integ:
        return {"status": "missing_integration"}
    resp = await integ.create_event(user_id=user_id, summary="Builder Test Event", start_iso=start, end_iso=end)  # type: ignore[attr-defined]
    return resp


class CreateEventRequest(BaseModel):
    summary: str
    start_iso: str
    end_iso: str
    timezone: str | None = None


@router.post("/google/calendar/create/{user_id}")
async def create_calendar_event(user_id: str, payload: CreateEventRequest):
    integ = hub.integrations.get("google_calendar")
    if not integ:
        return {"status": "missing_integration"}
    resp = await integ.create_event(  # type: ignore[attr-defined]
        user_id=user_id,
        summary=payload.summary,
        start_iso=payload.start_iso,
        end_iso=payload.end_iso,
        timezone_str=payload.timezone,
    )
    return resp


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str


@router.post("/google/gmail/send/{user_id}")
async def gmail_send(user_id: str, payload: SendEmailRequest):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.send_email(user_id, payload.to, payload.subject, payload.body)  # type: ignore[attr-defined]


class CreateDocRequest(BaseModel):
    title: str
    content: str


@router.post("/google/drive/create_doc/{user_id}")
async def drive_create_doc(user_id: str, payload: CreateDocRequest):
    integ = hub.integrations.get("google_drive")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.create_document(user_id, payload.title, payload.content)  # type: ignore[attr-defined]


@router.get("/google/gmail/labels/{user_id}")
async def gmail_labels(user_id: str):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.list_labels(user_id)  # type: ignore[attr-defined]


class CreateLabelRequest(BaseModel):
    name: str


@router.post("/google/gmail/labels/{user_id}")
async def gmail_create_label(user_id: str, payload: CreateLabelRequest):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.create_label(user_id, payload.name)  # type: ignore[attr-defined]


class MoveMessageRequest(BaseModel):
    message_id: str
    label: str


@router.post("/google/gmail/move/{user_id}")
async def gmail_move_message(user_id: str, payload: MoveMessageRequest):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.move_message_to_label(user_id, payload.message_id, payload.label)  # type: ignore[attr-defined]


class MoveDraftRequest(BaseModel):
    draft_id: str
    label: str


@router.post("/google/gmail/move_draft/{user_id}")
async def gmail_move_draft(user_id: str, payload: MoveDraftRequest):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    lookup = await integ.get_draft_message_id(user_id, payload.draft_id)
    if lookup.get("status") != "ok":
        return lookup
    mid = lookup.get("message_id")
    if not mid:
        return {"status": "error", "error": "missing_message_id"}
    return await integ.move_message_to_label(user_id, str(mid), payload.label)  # type: ignore[attr-defined]


@router.get("/google/people/contacts/{user_id}")
async def people_list_contacts(user_id: str):
    integ = hub.integrations.get("google_people")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.list_contacts(user_id)  # type: ignore[attr-defined]


class CreateContactRequest(BaseModel):
    name: str
    email: str


@router.post("/google/people/contacts/{user_id}")
async def people_create_contact(user_id: str, payload: CreateContactRequest):
    integ = hub.integrations.get("google_people")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.create_contact(user_id, payload.name, payload.email)  # type: ignore[attr-defined]


class DirectionsRequest(BaseModel):
    origin: str
    destination: str
    mode: str | None = None


@router.post("/google/maps/directions")
async def maps_directions(payload: DirectionsRequest):
    integ = hub.integrations.get("google_maps")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.directions(payload.origin, payload.destination, payload.mode or "driving")  # type: ignore[attr-defined]


@router.get("/google/maps/geocode")
async def maps_geocode(q: str):
    integ = hub.integrations.get("google_maps")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.geocode(q)  # type: ignore[attr-defined]


@router.get("/google/maps/places")
async def maps_places(query: str, location: str | None = None, radius: int | None = None):
    integ = hub.integrations.get("google_maps")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.places_search(query, location, radius)  # type: ignore[attr-defined]


class CreateTextFileRequest(BaseModel):
    name: str
    content: str


@router.post("/google/drive/create_text/{user_id}")
async def drive_create_text(user_id: str, payload: CreateTextFileRequest):
    integ = hub.integrations.get("google_drive")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.create_text_file(user_id, payload.name, payload.content)  # type: ignore[attr-defined]


class CreateDraftRequest(BaseModel):
    to: str
    subject: str
    body: str


@router.post("/google/gmail/draft/{user_id}")
async def gmail_draft(user_id: str, payload: CreateDraftRequest):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    return await integ.create_draft(user_id, payload.to, payload.subject, payload.body)  # type: ignore[attr-defined]


@router.get("/test/{user_id}")
async def test_integration(user_id: str):
    # Prefer mock if available
    if "mock_calendar" not in hub.integrations:
        try:
            from .mock_provider import MockCalendarIntegration

            hub.register("mock_calendar", MockCalendarIntegration())
        except Exception:
            pass
    if "mock_calendar" in hub.integrations:
        result = await hub.integrations["mock_calendar"].sync(user_id)
        return {"source": "mock", "result": result}
    # fallback to sync all
    return await hub.sync_all(user_id)


