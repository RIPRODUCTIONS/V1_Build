from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random
from typing import Any, Dict

from .base import IntegrationBase


class MockCalendarIntegration(IntegrationBase):
    name: str = "mock_calendar"

    async def discover(self, user_id: str) -> bool:
        return True

    async def sync(self, user_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        titles = [
            "Team Standup",
            "1:1 with Manager",
            "Product Review",
            "Lunch Break",
            "Client Call",
            "Sprint Planning",
        ]
        events = []
        for i in range(5):
            ts = now + timedelta(days=i, hours=random.randint(9, 17))
            events.append({
                "title": random.choice(titles),
                "when": ts.isoformat(),
                "user": user_id,
            })
        return {"status": "success", "events_synced": len(events), "events": events}


