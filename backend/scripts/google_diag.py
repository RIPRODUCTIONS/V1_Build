#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
import asyncio
import sys

import httpx

sys.path.insert(0, "/app")
from app.integrations.security import CredentialVault  # noqa: E402


async def main(user_id: str = "1") -> None:
    vault = CredentialVault.from_env()
    blob = vault.get(user_id, "google_calendar", "oauth")
    if not blob:
        print("no_credentials")
        return
    creds = json.loads(blob)
    headers = {"Authorization": f"Bearer {creds.get('access_token','')}"}
    now = datetime.now(timezone.utc)
    params = {
        "timeMin": (now - timedelta(days=1)).isoformat(),
        "timeMax": (now + timedelta(days=7)).isoformat(),
        "singleEvents": True,
        "orderBy": "startTime",
        "maxResults": 5,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=headers,
            params=params,
        )
        print("status", r.status_code)
        text = r.text
        print(text[:2000])


if __name__ == "__main__":
    asyncio.run(main())


