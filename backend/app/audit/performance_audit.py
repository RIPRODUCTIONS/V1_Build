from __future__ import annotations

from typing import Any, Dict


class PerformanceAuditor:
    async def system_resource_audit(self) -> Dict[str, Any]:
        return {"resources": {}, "status": "skipped"}

    async def application_performance_audit(self) -> Dict[str, Any]:
        return {"application": {}, "status": "skipped"}


