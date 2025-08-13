from typing import Any, Dict, List


class OperatorMonitoring:
    async def monitor_automation_health(self) -> Dict[str, Any]:
        return {
            "web_operator": "disabled",
            "desktop_operator": "disabled",
            "queues": {"high": 0, "normal": 0, "low": 0},
        }

    async def generate_automation_alerts(self, thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def generate_automation_analytics(self, time_period: str) -> Dict[str, Any]:
        return {"period": time_period, "status": "disabled"}


