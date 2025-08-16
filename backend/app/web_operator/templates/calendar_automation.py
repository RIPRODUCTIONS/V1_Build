from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.integrations.google_workspace import GoogleCalendarIntegration


class PersonalCalendarAutomation:
    template_config = {
        "id": "calendar_briefing",
        "name": "Personal Calendar Briefing",
        "category": "productivity",
        "description": "Analyze and brief your upcoming schedule",
    }

    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            user_id = str(parameters.get("user_id", "1"))
            cal = GoogleCalendarIntegration()
            now = datetime.now(UTC)
            creds = await cal.get_credentials(user_id)
            if not creds:
                return {"success": False, "detail": {"status": "missing_creds"}}
            items = await cal._list_events(user_id, creds, now, now + timedelta(days=7))
            if isinstance(items, dict) and items.get("status") == "error":
                return {"success": False, "detail": items}
            events: list[dict[str, Any]] = items if isinstance(items, list) else []
            analysis = await self._analyze_schedule(events)
            briefing = await self._generate_daily_briefing(events, analysis)
            optimizations = await self._suggest_schedule_optimizations(events)
            return {
                "success": True,
                "events_analyzed": len(events),
                "daily_briefing": briefing,
                "schedule_analysis": analysis,
                "optimizations": optimizations,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _analyze_schedule(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(events)
        all_day = sum(1 for e in events if e.get("start", {}).get("date"))
        return {"total": total, "all_day": all_day}

    async def _generate_daily_briefing(self, events: list[dict[str, Any]], analysis: dict[str, Any]) -> str:
        return f"You have {analysis.get('total', 0)} events in the next week; {analysis.get('all_day', 0)} all-day."

    async def _suggest_schedule_optimizations(self, events: list[dict[str, Any]]) -> list[str]:
        return ["Block 2 hours for focus work", "Add travel buffers between offsite meetings"]


