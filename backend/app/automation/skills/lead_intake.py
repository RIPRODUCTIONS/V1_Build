from typing import Any

from app.automation.registry import skill


@skill("lead.create_record")
async def create_lead(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "lead_created": True}


@skill("lead.schedule_followup")
async def schedule_followup(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "followup_scheduled": True}
