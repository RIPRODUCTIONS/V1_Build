from __future__ import annotations

from typing import Any


class ScalabilityAuditor:
    async def audit_horizontal_scaling(self) -> dict[str, Any]:
        return {"horizontal": {}, "status": "skipped"}

    async def audit_vertical_scaling(self) -> dict[str, Any]:
        return {"vertical": {}, "status": "skipped"}


