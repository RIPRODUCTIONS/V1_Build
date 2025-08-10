from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill("health.collect_biometrics")
async def collect_biometrics(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "biometrics": {"hr": 62, "hrv": 75, "sleep_score": 82}}


@skill("health.detect_anomaly")
async def detect_anomaly(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "anomaly": False}


@skill("health.trend_analyze")
async def trend_analyze(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "trend": {"hr": "stable", "sleep": "improving"}}


@skill("nutrition.analyze")
async def nutrition_analyze(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "calories": 2200, "macros": {"p": 140, "c": 200, "f": 70}}


@skill("nutrition.plan_meals")
async def nutrition_plan_meals(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "meal_plan": ["oats", "grilled chicken", "salad"]}
