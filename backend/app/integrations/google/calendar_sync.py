from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from app.automations.event_bus import publish_calendar_created
from app.db import SessionLocal
from app.integrations.google_workspace import OAuth2Credentials
from app.integrations.security import CredentialVault
from app.integrations.sync_models import CalendarSyncToken
from sqlalchemy.orm import Session


@dataclass(slots=True)
class CalendarDelta:
    added_or_updated: list[dict]
    deleted: list[str]
    next_sync_token: str | None


@dataclass(slots=True)
class CalendarIncrementalSync:
    """
    Incremental sync using Google's syncToken flow.
    Persists per-user per-calendar tokens; handles invalidation.
    """

    vault: CredentialVault = field(default_factory=CredentialVault.from_env)

    def _get_session(self) -> Session:
        return SessionLocal()

    def _get_creds(self, user_id: str) -> OAuth2Credentials | None:
        blob = self.vault.get(user_id, "google_calendar", "oauth")
        if not blob:
            return None
        try:
            data = __import__("json").loads(blob)
            return OAuth2Credentials(
                access_token=data.get("access_token", ""),
                refresh_token=data.get("refresh_token"),
                expires_at_ts=data.get("expires_at"),
            )
        except Exception:
            return None

    async def setup_incremental_sync(self, user_id: str, calendar_id: str = "primary") -> str | None:
        """
        Perform initial full sync to obtain a syncToken. Stores it and returns it.
        """
        creds = self._get_creds(user_id)
        if not creds:
            return None
        params: dict[str, str | int | float | bool | None] = {
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 100,
        }
        headers = {"Authorization": f"Bearer {creds.access_token}"}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                headers=headers,
                params=params,
            )
            if r.status_code >= 400:
                return None
            data = r.json()
            token = data.get("nextSyncToken")
            if token:
                db = self._get_session()
                try:
                    row = db.get(CalendarSyncToken, {"user_id": user_id, "calendar_id": calendar_id})
                except Exception:
                    row = None
                if row is None:
                    row = CalendarSyncToken(user_id=user_id, calendar_id=calendar_id, sync_token=token)
                    db.add(row)
                else:
                    # Assign to ORM attributes; mypy may not follow SQLA types
                    row.sync_token = token  # type: ignore[assignment]
                    row.updated_at = datetime.now(UTC)  # type: ignore[assignment]
                db.commit()
                db.close()
            return token

    async def get_calendar_delta(self, user_id: str, calendar_id: str = "primary") -> CalendarDelta | None:
        """
        Use stored syncToken to fetch changes. If token invalid, returns None (caller should re-setup).
        """
        creds = self._get_creds(user_id)
        if not creds:
            return None
        db = self._get_session()
        row = (
            db.query(CalendarSyncToken)
            .filter(CalendarSyncToken.user_id == user_id)
            .filter(CalendarSyncToken.calendar_id == calendar_id)
            .first()
        )
        if not row or not row.sync_token:
            db.close()
            await self.setup_incremental_sync(user_id, calendar_id)
            return None
        params: dict[str, str | int | float | bool | None] = {"syncToken": str(row.sync_token)}
        headers = {"Authorization": f"Bearer {creds.access_token}"}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                headers=headers,
                params=params,
            )
            if r.status_code == 410:
                # Token invalidated: caller must reinitialize
                row.sync_token = None  # type: ignore[assignment]
                db.commit()
                db.close()
                return None
            if r.status_code >= 400:
                db.close()
                return None
            data = r.json()
            items = data.get("items", [])
            added_or_updated: list[dict] = []
            deleted: list[str] = []
            for it in items:
                if it.get("status") == "cancelled" or it.get("cancelled"):
                    if it.get("id"):
                        deleted.append(it["id"])
                    continue
                added_or_updated.append(it)
            next_token = data.get("nextSyncToken")
            if next_token:
                row.sync_token = next_token  # type: ignore[assignment]
                row.updated_at = datetime.now(UTC)  # type: ignore[assignment]
                db.commit()
            db.close()
            return CalendarDelta(added_or_updated=added_or_updated, deleted=deleted, next_sync_token=next_token)

    async def process_delta_changes(self, user_id: str, delta: CalendarDelta) -> None:
        """
        Process delta events and emit to bus for automations.
        """
        now = datetime.now(UTC)
        for ev in delta.added_or_updated:
            payload = {
                "source": "google_calendar",
                "timestamp": now.isoformat(),
                "user_id": user_id,
                "event_type": "calendar",
                "raw_data": ev,
                "normalized_data": {
                    "title": ev.get("summary"),
                    "description": ev.get("description"),
                    "participants": [],
                    "tags": ["calendar"],
                },
            }
            await publish_calendar_created(user_id, payload, context={})
        # Deletions could trigger cleanup rules if desired


