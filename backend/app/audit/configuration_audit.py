from __future__ import annotations

from typing import Any


class ConfigurationAuditor:
    async def audit_environment_configurations(self) -> dict[str, Any]:
        return {"envs": {}, "status": "skipped"}

    async def audit_security_configurations(self) -> dict[str, Any]:
        return {"security": {}, "status": "skipped"}


