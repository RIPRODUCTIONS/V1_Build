from __future__ import annotations

from typing import Any, Dict


class ScalabilityAuditor:
    async def audit_horizontal_scaling(self) -> Dict[str, Any]:
        return {"horizontal": {}, "status": "skipped"}

    async def audit_vertical_scaling(self) -> Dict[str, Any]:
        return {"vertical": {}, "status": "skipped"}


