from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill("travel.find_deals")
async def find_deals(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "deals": [{"route": "SFO→JFK", "price": 299}]}


@skill("travel.build_itinerary")
async def build_itinerary(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "itinerary": ["fly", "hotel", "meetings"]}


@skill("travel.check_in_reminders")
async def check_in_reminders(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "reminders": ["check-in 24h"]}
