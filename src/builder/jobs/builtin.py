from __future__ import annotations

import json

from ..config import Settings
from . import register


@register("verify-resources")
def verify_resources() -> int:
    """Verify that core resource paths exist and are directories.

    Writes a JSON summary to stdout and returns 0 on success, 1 on failure.
    """
    settings = Settings.load()
    issues = settings.validate()

    summary = {
        "workspace_dir": str(settings.workspace_dir),
        "resource_drive": str(settings.resource_drive),
        "toolbox_20gb": str(settings.toolbox_20gb),
        "toolbox": str(settings.toolbox),
        "toolbox_backendr_2": str(settings.toolbox_backendr_2),
        "issues": issues,
    }
    print(json.dumps(summary, indent=2))
    return 0 if not issues else 1
