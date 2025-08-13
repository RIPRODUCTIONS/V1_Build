from __future__ import annotations

from typing import Any, Dict

from celery import shared_task

from app.operator.templates.research_automation import PersonalResearchAssistant
from app.operator.templates.shopping_automation import PersonalShoppingAssistant


@shared_task(name="personal.research.execute")
def execute_personal_research(task_data: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio

    async def _run() -> Dict[str, Any]:
        assistant = PersonalResearchAssistant()
        return await assistant.execute(task_data or {})

    return asyncio.run(_run())


@shared_task(name="personal.shopping.execute")
def execute_personal_shopping(task_data: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio

    async def _run() -> Dict[str, Any]:
        assistant = PersonalShoppingAssistant()
        return await assistant.execute(task_data or {})

    return asyncio.run(_run())


