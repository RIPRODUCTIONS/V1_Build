from __future__ import annotations

from typing import Any


def route_task(task: dict[str, Any]) -> str:
    t = (task.get("task_type") or "").lower()
    if "invoice" in t or "finance" in t:
        return "finance_ai_accountant"
    if "lead" in t or "sales" in t:
        return "ai_sales_manager"
    if "content" in t or "marketing" in t:
        return "ai_marketing_manager"
    return "executive_chief_of_staff"




