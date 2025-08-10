from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill("home.presence_detect")
async def presence_detect(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "presence": True}


@skill("home.scene_evening")
async def scene_evening(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "scene": "evening"}


@skill("home.energy_optimize")
async def energy_optimize(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "energy_saving": 0.12}
