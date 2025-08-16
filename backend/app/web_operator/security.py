from typing import Any


class OperatorSecurity:
    async def validate_automation_security(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"validated": True, "status": "disabled"}

    async def audit_automation_actions(self, task_id: str, actions: list[dict[str, Any]]) -> None:
        return None


