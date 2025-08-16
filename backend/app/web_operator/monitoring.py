from typing import Any


class OperatorMonitoring:
    async def monitor_automation_health(self) -> dict[str, Any]:
        return {
            "web_operator": "disabled",
            "desktop_operator": "disabled",
            "queues": {"high": 0, "normal": 0, "low": 0},
        }

    async def generate_automation_alerts(self, thresholds: dict[str, Any]) -> list[dict[str, Any]]:
        return []

    async def generate_automation_analytics(self, time_period: str) -> dict[str, Any]:
        return {"period": time_period, "status": "disabled"}


