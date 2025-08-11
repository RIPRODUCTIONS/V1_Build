from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill("calendar.find_slots")
async def find_slots(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "slots": ["09:00", "11:00", "15:00"]}


@skill("calendar.schedule_tasks")
async def schedule_tasks(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "scheduled_tasks": ["standup", "review"]}


@skill("calendar.auto_followups")
async def auto_followups(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "followups": ["send summary"]}
