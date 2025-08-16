from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

from .base import IntegrationBase, OAuth2Integration, OAuth2Credentials
from .models import UnifiedEvent, NormalizedEventData
from .security import CredentialVault
from app.core.config import get_settings
from app.automations.event_bus import publish_calendar_created
from prometheus_client import Counter


@dataclass(slots=True)
class GoogleCalendarIntegration(OAuth2Integration):
    name: str = "google_calendar"

    def __init__(self) -> None:
        # Ensure dataclass field `name` is initialized when overriding __init__
        self.name = "google_calendar"
        self.vault = CredentialVault.from_env()
        self.settings = get_settings()
        # metrics
        self.metric_requests = Counter(
            "google_calendar_requests_total",
            "Total Google Calendar API requests",
            labelnames=("method", "endpoint", "status"),
        )
        self.metric_errors = Counter(
            "google_calendar_errors_total",
            "Total Google Calendar API errors",
            labelnames=("method", "endpoint", "code"),
        )

    async def get_credentials(self, user_id: str) -> OAuth2Credentials | None:
        blob = self.vault.get(user_id, self.name, "oauth")
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

    async def refresh(self, creds: OAuth2Credentials) -> OAuth2Credentials:
        # Base method required by OAuth2Integration; not user-specific here
        return creds

    async def refresh_for_user(self, user_id: str, creds: OAuth2Credentials) -> OAuth2Credentials:
        # Basic token refresh flow
        if not self.settings.GOOGLE_CLIENT_ID or not self.settings.GOOGLE_CLIENT_SECRET or not creds.refresh_token:
            return creds
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.settings.GOOGLE_CLIENT_ID,
                    "client_secret": self.settings.GOOGLE_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": creds.refresh_token,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                new = OAuth2Credentials(
                    access_token=data.get("access_token", creds.access_token),
                    refresh_token=creds.refresh_token,
                    expires_at_ts=int(datetime.now(timezone.utc).timestamp()) + int(data.get("expires_in", 3600)),
                )
                # persist back
                self.vault.put(user_id, self.name, "oauth", __import__("json").dumps({
                    "access_token": new.access_token,
                    "refresh_token": new.refresh_token,
                    "expires_at": new.expires_at_ts,
                }))
                return new
        return creds

    async def discover(self, user_id: str) -> bool:
        return self.get_credentials is not None and bool(self.vault.get(user_id, self.name, "oauth"))

    async def _auth_headers(self, creds: OAuth2Credentials) -> Dict[str, str]:
        return {"Authorization": f"Bearer {creds.access_token}"}

    async def _list_events(self, user_id: str, creds: OAuth2Credentials, time_min: datetime, time_max: datetime) -> list[dict] | Dict[str, Any]:
        params: Dict[str, str | int | float | bool | None] = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 100,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=await self._auth_headers(creds),
                params=params,
            )
            self.metric_requests.labels("GET", "/events", str(r.status_code)).inc()
            if r.status_code == 401 and creds.refresh_token:
                creds = await self.refresh_for_user(user_id, creds)
                r = await client.get(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers=await self._auth_headers(creds),
                    params=params,
                )
                self.metric_requests.labels("GET", "/events", str(r.status_code)).inc()
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Log rich error for diagnosis
                detail = {
                    "status": r.status_code,
                    "text": r.text[:500],
                }
                self.metric_errors.labels("GET", "/events", str(r.status_code)).inc()
                return {"status": "error", "error": detail}
            data = r.json()
            return data.get("items", [])

    async def create_event(
        self,
        user_id: str,
        summary: str,
        start_iso: str,
        end_iso: str,
        timezone_str: str | None = None,
    ) -> Dict[str, Any]:
        creds = await self.get_credentials(user_id)
        if not creds:
            return {"status": "missing_creds"}
        body: Dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start_iso},
            "end": {"dateTime": end_iso},
        }
        if timezone_str:
            body["start"]["timeZone"] = timezone_str
            body["end"]["timeZone"] = timezone_str

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=await self._auth_headers(creds),
                json=body,
            )
            self.metric_requests.labels("POST", "/events", str(r.status_code)).inc()
            if r.status_code == 401 and creds.refresh_token:
                creds = await self.refresh_for_user(user_id, creds)
                r = await client.post(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers=await self._auth_headers(creds),
                    json=body,
                )
                self.metric_requests.labels("POST", "/events", str(r.status_code)).inc()
            if r.status_code >= 400:
                # simple retry once on 429/5xx
                if r.status_code in (429, 500, 502, 503, 504):
                    await __import__("asyncio").sleep(1.0)
                    r = await client.post(
                        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                        headers=await self._auth_headers(creds),
                        json=body,
                    )
                    self.metric_requests.labels("POST", "/events", str(r.status_code)).inc()
                if r.status_code >= 400:
                    self.metric_errors.labels("POST", "/events", str(r.status_code)).inc()
                    return {"status": "error", "error": {"code": r.status_code, "body": r.text[:800]}}
            data = r.json()
            return {"status": "ok", "id": data.get("id"), "htmlLink": data.get("htmlLink")}

    async def sync(self, user_id: str) -> Dict[str, Any]:
        if not self.settings.GOOGLE_CALENDAR_SYNC:
            return {"status": "disabled"}
        creds = await self.get_credentials(user_id)
        if not creds:
            return {"status": "missing_creds"}
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=7)
        window_end = now + timedelta(days=30)
        items = await self._list_events(user_id, creds, window_start, window_end)
        if isinstance(items, dict) and items.get("status") == "error":
            return items
        normalized: list[UnifiedEvent] = []
        for it in items if isinstance(items, list) else []:
            start = it.get("start", {}).get("dateTime") or it.get("start", {}).get("date")
            ts = datetime.fromisoformat(start.replace("Z", "+00:00")) if start else now
            ned = NormalizedEventData(title=it.get("summary"), description=it.get("description"), participants=[], tags=["calendar"])
            normalized.append(
                UnifiedEvent(
                    source=self.name,
                    timestamp=ts,
                    user_id=user_id,
                    event_type="calendar",
                    raw_data=it,
                    normalized_data=ned,
                )
            )
        # Publish to automation event bus (best-effort) and hand off to rule evaluator
        try:
            for ev in normalized:
                data = ev.model_dump()
                await publish_calendar_created(user_id, data, context={})
        except Exception:
            pass
        return {"status": "ok", "events_synced": len(normalized)}


@dataclass(slots=True)
class GmailIntegration(IntegrationBase):
    name: str = "gmail"

    async def discover(self, user_id: str) -> bool:
        # Reuse Google OAuth vault; if calendar creds exist we assume user intends Google
        try:
            v = CredentialVault.from_env()
            return bool(v.get(user_id, "google_calendar", "oauth"))
        except Exception:
            return False

    async def sync(self, user_id: str) -> Dict[str, Any]:
        # Best-effort: only run if token present and has Gmail scope; otherwise skip gracefully
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}

        headers = {"Authorization": f"Bearer {access_token}"}
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        params = {"maxResults": 10}
        # metrics
        metric_requests = Counter(
            "gmail_requests_total",
            "Total Gmail API requests",
            labelnames=("endpoint", "status"),
        )
        metric_errors = Counter(
            "gmail_errors_total",
            "Total Gmail API errors",
            labelnames=("endpoint", "code"),
        )
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            metric_requests.labels("/messages", str(r.status_code)).inc()
            if r.status_code == 401:
                return {"status": "auth_error"}
            if r.status_code == 403:
                # Likely missing scope; treat as skipped
                metric_errors.labels("/messages", str(r.status_code)).inc()
                return {"status": "skipped_missing_scope"}
            if r.status_code >= 400:
                metric_errors.labels("/messages", str(r.status_code)).inc()
                return {"status": "error", "code": r.status_code}
            payload = r.json()
            count = len(payload.get("messages", []))
            return {"status": "ok", "emails_scanned": count}

    async def send_email(self, user_id: str, to_email: str, subject: str, body_text: str) -> Dict[str, Any]:
        """Send an email using Gmail API.

        Requires scope https://www.googleapis.com/auth/gmail.send
        """
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}

        import base64

        raw_message = (
            f"To: {to_email}\r\n"
            f"Subject: {subject}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{body_text}"
        ).encode("utf-8")
        b64_message = base64.urlsafe_b64encode(raw_message).decode("utf-8")

        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, headers=headers, json={"raw": b64_message})
            if r.status_code == 403:
                return {"status": "skipped_missing_scope", "code": 403}
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            data = r.json()
            return {"status": "ok", "id": data.get("id")}

    async def create_draft(self, user_id: str, to_email: str, subject: str, body_text: str) -> Dict[str, Any]:
        """Create an email draft using Gmail API.

        Requires scope https://www.googleapis.com/auth/gmail.compose or gmail.modify
        """
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}

        import base64

        raw_message = (
            f"To: {to_email}\r\n"
            f"Subject: {subject}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{body_text}"
        ).encode("utf-8")
        b64_message = base64.urlsafe_b64encode(raw_message).decode("utf-8")

        url = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, headers=headers, json={"message": {"raw": b64_message}})
            if r.status_code == 403:
                return {"status": "skipped_missing_scope", "code": 403}
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            data = r.json()
            return {"status": "ok", "id": data.get("id")}

    async def get_draft_message_id(self, user_id: str, draft_id: str) -> Dict[str, Any]:
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/drafts/{draft_id}"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers)
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:300]}
            payload = r.json()
            msg = (payload or {}).get("message") or {}
            mid = msg.get("id")
            return {"status": "ok", "message_id": mid}

    async def list_labels(self, user_id: str) -> Dict[str, Any]:
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}
        url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 403:
                return {"status": "skipped_missing_scope", "code": 403}
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:300]}
            return {"status": "ok", "labels": r.json().get("labels", [])}

    async def create_label(self, user_id: str, name: str) -> Dict[str, Any]:
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}
        url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"
        headers = {"Authorization": f"Bearer {access_token}"}
        body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, headers=headers, json=body)
            if r.status_code == 403:
                return {"status": "skipped_missing_scope", "code": 403}
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:300]}
            return {"status": "ok", "label": r.json()}

    async def list_messages(self, user_id: str, q: str | None = None, max_results: int = 10) -> Dict[str, Any]:
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}
        headers = {"Authorization": f"Bearer {access_token}"}
        params: Dict[str, Any] = {"maxResults": max_results}
        if q:
            params["q"] = q
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:300]}
            return {"status": "ok", "messages": r.json().get("messages", [])}

    async def modify_message_labels(self, user_id: str, message_id: str, add_labels: list[str] | None = None, remove_labels: list[str] | None = None) -> Dict[str, Any]:
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}
        headers = {"Authorization": f"Bearer {access_token}"}
        body: Dict[str, Any] = {"addLabelIds": add_labels or [], "removeLabelIds": remove_labels or []}
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, headers=headers, json=body)
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:300]}
            return {"status": "ok", "message": r.json()}

    async def move_message_to_label(self, user_id: str, message_id: str, label_name: str) -> Dict[str, Any]:
        # Ensure label exists
        labels = await self.list_labels(user_id)
        if labels.get("status") != "ok":
            return labels
        id_map = {l.get("name"): l.get("id") for l in labels.get("labels", [])}
        label_id = id_map.get(label_name)
        if not label_id:
            created = await self.create_label(user_id, label_name)
            if created.get("status") != "ok":
                return created
            label_id = created.get("label", {}).get("id")
        # Move: add target label, optionally remove INBOX
        return await self.modify_message_labels(user_id, message_id, add_labels=[label_id], remove_labels=["INBOX"])


@dataclass(slots=True)
class GoogleDriveIntegration(IntegrationBase):
    name: str = "google_drive"

    async def discover(self, user_id: str) -> bool:
        try:
            v = CredentialVault.from_env()
            return bool(v.get(user_id, "google_calendar", "oauth"))
        except Exception:
            return False

    async def sync(self, user_id: str) -> Dict[str, Any]:
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}

        headers = {"Authorization": f"Bearer {access_token}"}
        url = "https://www.googleapis.com/drive/v3/files"
        params: Dict[str, str | int | float | bool | None] = {"pageSize": 10, "fields": "files(id,name,modifiedTime)"}
        metric_requests = Counter(
            "gdrive_requests_total",
            "Total Google Drive API requests",
            labelnames=("endpoint", "status"),
        )
        metric_errors = Counter(
            "gdrive_errors_total",
            "Total Google Drive API errors",
            labelnames=("endpoint", "code"),
        )
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            metric_requests.labels("/files", str(r.status_code)).inc()
            if r.status_code == 401:
                return {"status": "auth_error"}
            if r.status_code == 403:
                metric_errors.labels("/files", str(r.status_code)).inc()
                return {"status": "skipped_missing_scope"}
            if r.status_code >= 400:
                metric_errors.labels("/files", str(r.status_code)).inc()
                return {"status": "error", "code": r.status_code}
            payload = r.json()
            count = len(payload.get("files", []))
            return {"status": "ok", "files_indexed": count}

    async def create_document(self, user_id: str, title: str, content: str) -> Dict[str, Any]:
        """Create a Google Doc with initial text content using Drive convert upload.

        Requires Drive scope (e.g., https://www.googleapis.com/auth/drive.file)
        """
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}

        boundary = "===============7330845974216740156=="
        metadata = {"name": title, "mimeType": "application/vnd.google-apps.document"}
        parts = []
        parts.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + __import__("json").dumps(metadata) + "\r\n")
        parts.append(f"--{boundary}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n" + content + "\r\n")
        parts.append(f"--{boundary}--\r\n")
        body = "".join(parts)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        }
        url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, headers=headers, content=body.encode("utf-8"))
            if r.status_code == 403:
                return {"status": "skipped_missing_scope", "code": 403}
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            data = r.json()
            return {"status": "ok", "id": data.get("id")}

    async def create_text_file(self, user_id: str, name: str, content: str) -> Dict[str, Any]:
        """Create a plain text file in Drive using multipart upload.

        Requires Drive file scope.
        """
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}

        boundary = "===============7330845974216740157=="
        metadata = {"name": name, "mimeType": "text/plain"}
        parts = []
        parts.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + __import__("json").dumps(metadata) + "\r\n")
        parts.append(f"--{boundary}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n" + content + "\r\n")
        parts.append(f"--{boundary}--\r\n")
        body = "".join(parts)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        }
        url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, headers=headers, content=body.encode("utf-8"))
            if r.status_code == 403:
                return {"status": "skipped_missing_scope", "code": 403}
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            data = r.json()
            return {"status": "ok", "id": data.get("id")}


@dataclass(slots=True)
class GooglePeopleIntegration(IntegrationBase):
    name: str = "google_people"

    async def discover(self, user_id: str) -> bool:
        try:
            v = CredentialVault.from_env()
            return bool(v.get(user_id, "google_calendar", "oauth"))
        except Exception:
            return False

    async def list_contacts(self, user_id: str, page_size: int = 10) -> Dict[str, Any]:
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}
        headers = {"Authorization": f"Bearer {access_token}"}
        params: Dict[str, str | int | float | bool | None] = {"personFields": "names,emailAddresses", "pageSize": page_size}
        url = "https://people.googleapis.com/v1/people/me/connections"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code == 403:
                return {"status": "skipped_missing_scope", "code": 403}
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            return {"status": "ok", "connections": r.json().get("connections", [])}

    async def create_contact(self, user_id: str, name: str, email: str) -> Dict[str, Any]:
        v = CredentialVault.from_env()
        blob = v.get(user_id, "google_calendar", "oauth")
        if not blob:
            return {"status": "missing_creds"}
        try:
            data = __import__("json").loads(blob)
            access_token = data.get("access_token", "")
        except Exception:
            return {"status": "missing_creds"}
        headers = {"Authorization": f"Bearer {access_token}"}
        url = "https://people.googleapis.com/v1/people:createContact"
        body = {
            "names": [{"givenName": name}],
            "emailAddresses": [{"value": email}],
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, headers=headers, json=body)
            if r.status_code == 403:
                return {"status": "skipped_missing_scope", "code": 403}
            if r.status_code >= 400:
                return {"status": "error", "code": r.status_code, "body": r.text[:400]}
            return {"status": "ok", "person": r.json()}


