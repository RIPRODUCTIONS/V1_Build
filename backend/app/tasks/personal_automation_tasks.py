from __future__ import annotations

from typing import Any, Dict

from celery import shared_task

from app.operator.templates.research_automation import PersonalResearchAssistant
from app.operator.templates.shopping_automation import PersonalShoppingAssistant
from app.operator.templates.email_automation import PersonalEmailAutomation as PersonalEmailManager  # type: ignore
from app.operator.templates.calendar_automation import PersonalCalendarAutomation as PersonalFinanceTracker  # type: ignore
from app.operator.templates.social_automation import PersonalSocialMediaManager  # new


@shared_task(name="personal.research.execute")
def execute_personal_research(task_data: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio

    async def _run() -> Dict[str, Any]:
        assistant = PersonalResearchAssistant()
        try:
            return await assistant.execute(task_data or {})
        except ModuleNotFoundError as e:
            return {"success": False, "reason": str(e)}

    return asyncio.run(_run())


@shared_task(name="personal.shopping.execute")
def execute_personal_shopping(task_data: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio

    async def _run() -> Dict[str, Any]:
        assistant = PersonalShoppingAssistant()
        try:
            return await assistant.execute(task_data or {})
        except ModuleNotFoundError as e:
            return {"success": False, "reason": str(e)}

    return asyncio.run(_run())


@shared_task(name="personal.social.execute")
def execute_personal_social(task_data: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio

    async def _run() -> Dict[str, Any]:
        assistant = PersonalSocialMediaManager()
        return await assistant.execute(task_data or {})

    return asyncio.run(_run())


@shared_task(name="personal.email.execute")
def execute_personal_email(task_data: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio

    async def _run() -> Dict[str, Any]:
        try:
            assistant = PersonalEmailManager()
        except Exception:
            # fallback return when integration not present
            return {"success": False, "reason": "email_manager_not_available"}
        return await assistant.execute(task_data or {})

    return asyncio.run(_run())


@shared_task(name="personal.finance.execute")
def execute_personal_finance(task_data: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio

    async def _run() -> Dict[str, Any]:
        try:
            assistant = PersonalFinanceTracker()
        except Exception:
            return {"success": False, "reason": "finance_tracker_not_available"}
        return await assistant.execute(task_data or {})

    return asyncio.run(_run())


