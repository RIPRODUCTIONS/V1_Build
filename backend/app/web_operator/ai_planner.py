from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings

PROMPT_TEMPLATE = (
    "You are an expert web automation planner. Create a detailed step-by-step plan for this task:\n\n"
    "Task: {task_description}\n"
    "Target URL: {target_url}\n\n"
    "Return a JSON plan with this structure:\n"
    "{\n"
    "    \"steps\": [\n"
    "        {\n"
    "            \"action\": \"navigate\",\n"
    "            \"target\": \"https://example.com\",\n"
    "            \"description\": \"Navigate to the website\"\n"
    "        }\n"
    "    ],\n"
    "    \"success_criteria\": \"Form submitted successfully\",\n"
    "    \"estimated_duration\": \"2-3 minutes\"\n"
    "}\n"
)


class AIPlanner:
    async def create_plan(self, task_description: str, target_url: str | None) -> dict[str, Any]:
        settings = get_settings()
        if settings.OPERATOR_AI_ENABLED and settings.OPENAI_API_KEY:
            try:
                from app.services.llm.providers.openai_p import OpenAIProvider

                provider = OpenAIProvider(settings)
                prompt = PROMPT_TEMPLATE.format(task_description=task_description, target_url=target_url or "")
                raw = await provider.chat(prompt, system="You are an expert web automation planner.")
                plan = json.loads(raw)
                if isinstance(plan, dict) and "steps" in plan:
                    return plan
            except Exception:
                pass
        # Fallback stub plan
        steps: list[dict[str, Any]] = []
        if target_url:
            steps.append({"action": "navigate", "target": target_url, "description": "Navigate to target"})
        return {"steps": steps, "success_criteria": "completed", "estimated_duration": "1-3 minutes"}

# Removed duplicate AIPlanner definition


