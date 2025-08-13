from __future__ import annotations

from typing import Any, Dict


class DependencyAuditor:
    async def audit_package_dependencies(self) -> Dict[str, Any]:
        return {"packages": {}, "status": "skipped"}

    async def audit_runtime_dependencies(self) -> Dict[str, Any]:
        return {"runtime": {}, "status": "skipped"}


