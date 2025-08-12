from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill('learning.assess_skills')
async def assess_skills(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'skills': {'python': 'intermediate', 'ml': 'beginner'}}


@skill('learning.plan_path')
async def plan_path(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'plan': ['numpy', 'pandas', 'sklearn']}


@skill('learning.schedule')
async def schedule(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'schedule': {'mon': 'numpy', 'tue': 'pandas'}}
