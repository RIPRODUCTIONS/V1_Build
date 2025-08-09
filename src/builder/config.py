from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .paths import (
    get_resource_drive_path,
    get_toolbox_20gb_path,
    get_toolbox_backendr_2_path,
    get_toolbox_path,
    get_workspace_dir,
)


@dataclass(frozen=True)
class Settings:
    """Strongly-typed settings for the builder system.

    Paths are resolved from the environment (.env) or symlink fallbacks in `toolkits/`.
    """

    workspace_dir: Path
    resource_drive: Path
    toolbox_20gb: Path
    toolbox: Path
    toolbox_backendr_2: Path

    @staticmethod
    def load() -> Settings:
        # Load .env from workspace if present
        load_dotenv(get_workspace_dir() / ".env")
        return Settings(
            workspace_dir=get_workspace_dir(),
            resource_drive=get_resource_drive_path(),
            toolbox_20gb=get_toolbox_20gb_path(),
            toolbox=get_toolbox_path(),
            toolbox_backendr_2=get_toolbox_backendr_2_path(),
        )

    def validate(self) -> list[str]:
        """Return a list of validation issues; empty if all good."""
        issues: list[str] = []
        for label, path in self.as_dict().items():
            if label == "workspace_dir":
                continue
            if not path.exists():
                issues.append(f"Missing path: {label} -> {path}")
            elif not path.is_dir():
                issues.append(f"Not a directory: {label} -> {path}")
        return issues

    def as_dict(self) -> dict[str, Path]:
        return {
            "workspace_dir": self.workspace_dir,
            "resource_drive": self.resource_drive,
            "toolbox_20gb": self.toolbox_20gb,
            "toolbox": self.toolbox,
            "toolbox_backendr_2": self.toolbox_backendr_2,
        }


def summarize(settings: Settings) -> dict[str, Any]:
    return {
        "workspace_dir": str(settings.workspace_dir),
        "resource_drive": str(settings.resource_drive),
        "toolbox_20gb": str(settings.toolbox_20gb),
        "toolbox": str(settings.toolbox),
        "toolbox_backendr_2": str(settings.toolbox_backendr_2),
        "issues": settings.validate(),
    }
