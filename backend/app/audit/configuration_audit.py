from __future__ import annotations

from typing import Any, Dict


class ConfigurationAuditor:
    async def audit_environment_configurations(self) -> Dict[str, Any]:
        return {"envs": {}, "status": "skipped"}

    async def audit_security_configurations(self) -> Dict[str, Any]:
        return {"security": {}, "status": "skipped"}


