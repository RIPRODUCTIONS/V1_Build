from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Protocol, cast, runtime_checkable

from fastapi import APIRouter
from pydantic import BaseModel

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
            GmailIntegration,
            GoogleCalendarIntegration,
            GoogleDriveIntegration,
        )
        # Only register non-abstract integrations here
        hub.register("google_calendar", GoogleCalendarIntegration())
        hub.register("gmail", GmailIntegration())
        hub.register("google_drive", GoogleDriveIntegration())
    except Exception:
        # Silently skip if Google libs not available; we operate with mocks only
        pass
@runtime_checkable
class CalendarAPI(Protocol):
    async def create_event(self, user_id: str, summary: str, start_iso: str, end_iso: str, timezone_str: str | None = None) -> dict: ...


@runtime_checkable
class GmailAPI(Protocol):
    async def send_email(self, user_id: str, to_email: str, subject: str, body_text: str) -> dict: ...
    async def list_labels(self, user_id: str) -> dict: ...
    async def create_label(self, user_id: str, name: str) -> dict: ...
    async def get_draft_message_id(self, user_id: str, draft_id: str) -> dict: ...
    async def move_message_to_label(self, user_id: str, message_id: str, label_name: str) -> dict: ...
    async def create_draft(self, user_id: str, to_email: str, subject: str, body_text: str) -> dict: ...


@runtime_checkable
class DriveAPI(Protocol):
    async def create_document(self, user_id: str, title: str, content: str) -> dict: ...
    async def create_text_file(self, user_id: str, name: str, content: str) -> dict: ...


@runtime_checkable
class PeopleAPI(Protocol):
    async def list_contacts(self, user_id: str) -> dict: ...
    async def create_contact(self, user_id: str, name: str, email: str) -> dict: ...


@runtime_checkable
class MapsAPI(Protocol):
    async def directions(self, origin: str, destination: str, mode: str = "driving") -> dict: ...
    async def geocode(self, address: str) -> dict: ...
    async def places_search(self, query: str, location: str | None = None, radius: int | None = None) -> dict: ...




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
    now = datetime.now(UTC)
    start = (now + timedelta(minutes=5)).isoformat()
    end = (now + timedelta(minutes=35)).isoformat()
    integ = hub.integrations.get("google_calendar")
    if not integ:
        return {"status": "missing_integration"}
    # Narrow to expected interface at runtime
    cal = cast(CalendarAPI, integ)
    resp = await cal.create_event(user_id=user_id, summary="Builder Test Event", start_iso=start, end_iso=end)
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
    # Attribute available on concrete integration at runtime
    gmail = cast(GmailAPI, integ)
    return await gmail.send_email(user_id, payload.to, payload.subject, payload.body)


class CreateDocRequest(BaseModel):
    title: str
    content: str


@router.post("/google/drive/create_doc/{user_id}")
async def drive_create_doc(user_id: str, payload: CreateDocRequest):
    integ = hub.integrations.get("google_drive")
    if not integ:
        return {"status": "missing_integration"}
    drive = cast(DriveAPI, integ)
    return await drive.create_document(user_id, payload.title, payload.content)


@router.get("/google/gmail/labels/{user_id}")
async def gmail_labels(user_id: str):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    gmail = cast(GmailAPI, integ)
    return await gmail.list_labels(user_id)


class CreateLabelRequest(BaseModel):
    name: str


@router.post("/google/gmail/labels/{user_id}")
async def gmail_create_label(user_id: str, payload: CreateLabelRequest):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    gmail = cast(GmailAPI, integ)
    return await gmail.create_label(user_id, payload.name)


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
    gmail = cast(GmailAPI, integ)
    lookup = await gmail.get_draft_message_id(user_id, payload.draft_id)
    if lookup.get("status") != "ok":
        return lookup
    mid = lookup.get("message_id")
    if not mid:
        return {"status": "error", "error": "missing_message_id"}
    gmail = cast(GmailAPI, integ)
    return await gmail.move_message_to_label(user_id, str(mid), payload.label)


@router.get("/google/people/contacts/{user_id}")
async def people_list_contacts(user_id: str):
    integ = hub.integrations.get("google_people")
    if not integ:
        return {"status": "missing_integration"}
    people = cast(PeopleAPI, integ)
    return await people.list_contacts(user_id)


class CreateContactRequest(BaseModel):
    name: str
    email: str


@router.post("/google/people/contacts/{user_id}")
async def people_create_contact(user_id: str, payload: CreateContactRequest):
    integ = hub.integrations.get("google_people")
    if not integ:
        return {"status": "missing_integration"}
    people = cast(PeopleAPI, integ)
    return await people.create_contact(user_id, payload.name, payload.email)


class DirectionsRequest(BaseModel):
    origin: str
    destination: str
    mode: str | None = None


@router.post("/google/maps/directions")
async def maps_directions(payload: DirectionsRequest):
    integ = hub.integrations.get("google_maps")
    if not integ:
        return {"status": "missing_integration"}
    maps = cast(MapsAPI, integ)
    return await maps.directions(payload.origin, payload.destination, payload.mode or "driving")


@router.get("/google/maps/geocode")
async def maps_geocode(q: str):
    integ = hub.integrations.get("google_maps")
    if not integ:
        return {"status": "missing_integration"}
    maps = cast(MapsAPI, integ)
    return await maps.geocode(q)


@router.get("/google/maps/places")
async def maps_places(query: str, location: str | None = None, radius: int | None = None):
    integ = hub.integrations.get("google_maps")
    if not integ:
        return {"status": "missing_integration"}
    maps = cast(MapsAPI, integ)
    return await maps.places_search(query, location, radius)


class CreateTextFileRequest(BaseModel):
    name: str
    content: str


@router.post("/google/drive/create_text/{user_id}")
async def drive_create_text(user_id: str, payload: CreateTextFileRequest):
    integ = hub.integrations.get("google_drive")
    if not integ:
        return {"status": "missing_integration"}
    drive = cast(DriveAPI, integ)
    return await drive.create_text_file(user_id, payload.name, payload.content)


class CreateDraftRequest(BaseModel):
    to: str
    subject: str
    body: str


@router.post("/google/gmail/draft/{user_id}")
async def gmail_draft(user_id: str, payload: CreateDraftRequest):
    integ = hub.integrations.get("gmail")
    if not integ:
        return {"status": "missing_integration"}
    gmail = cast(GmailAPI, integ)
    return await gmail.create_draft(user_id, payload.to, payload.subject, payload.body)


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


