from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill('transport.plan_route')
async def plan_route(context: dict[str, Any]) -> dict[str, Any]:
    src = context.get('src', 'home')
    dst = context.get('dst', 'work')
    return {**context, 'route': [src, 'highway', dst]}


@skill('transport.optimize_cost')
async def optimize_cost(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'cost_estimate': 8.75}
