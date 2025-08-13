from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.integrations.google_workspace import GoogleCalendarIntegration


class PersonalCalendarAutomation:
    template_config = {
        "id": "calendar_briefing",
        "name": "Personal Calendar Briefing",
        "category": "productivity",
        "description": "Analyze and brief your upcoming schedule",
    }

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_id = str(parameters.get("user_id", "1"))
            cal = GoogleCalendarIntegration()
            now = datetime.now(timezone.utc)
            items = await cal._list_events(user_id, await cal.get_credentials(user_id) or cal.get_credentials, now, now + timedelta(days=7))
            if isinstance(items, dict) and items.get("status") == "error":
                return {"success": False, "detail": items}
            events: List[Dict[str, Any]] = items if isinstance(items, list) else []
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

    async def _analyze_schedule(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(events)
        all_day = sum(1 for e in events if e.get("start", {}).get("date"))
        return {"total": total, "all_day": all_day}

    async def _generate_daily_briefing(self, events: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        return f"You have {analysis.get('total', 0)} events in the next week; {analysis.get('all_day', 0)} all-day."

    async def _suggest_schedule_optimizations(self, events: List[Dict[str, Any]]) -> List[str]:
        return ["Block 2 hours for focus work", "Add travel buffers between offsite meetings"]


