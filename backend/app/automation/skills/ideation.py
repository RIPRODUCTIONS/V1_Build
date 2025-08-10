from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill("ideation.generate")
async def generate_ideas(context: dict[str, Any]) -> dict[str, Any]:
    topic = (context.get("topic") or "general").strip()
    count = int(context.get("count") or 5)
    # Lightweight deterministic ideas to avoid external dependencies
    seeds = [
        f"AI assistant for {topic} workflows",
        f"Cost optimizer for {topic} using simple heuristics",
        f"Compliance checker for {topic} with rule templates",
        f"Dashboard for {topic} KPIs with alerting",
        f"Automation scripts to eliminate manual steps in {topic}",
    ]
    ideas = seeds[: max(1, min(count, 10))]
    return {**context, "ideas": ideas}
