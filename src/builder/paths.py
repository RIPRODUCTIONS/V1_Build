from __future__ import annotations

import os
from pathlib import Path


def get_workspace_dir() -> Path:
    """Return the project workspace directory (repository root)."""
    # This file lives at <root>/src/builder/paths.py → parents[2] is <root>
    return Path(__file__).resolve().parents[2]


def get_toolkits_dir() -> Path:
    """Return the `toolkits` directory containing symlinks to external resources."""
    return get_workspace_dir() / "toolkits"


def _env_or_symlink(env_var_name: str, symlink_name: str) -> Path:
    """Resolve a path from environment variable or fallback to a symlink in toolkits.

    - If the env var is set, use it.
    - Otherwise, use `<workspace>/toolkits/<symlink_name>`.
    """
    env_val = os.getenv(env_var_name)
    if env_val:
        return Path(env_val).expanduser().resolve()
    return (get_toolkits_dir() / symlink_name).resolve()


def get_resource_drive_path() -> Path:
    return _env_or_symlink("AI_PROJECT_RESOURCE_DRIVE", "resource_drive")


def get_toolbox_20gb_path() -> Path:
    return _env_or_symlink("AI_TOOLBOX_20GB_PATH", "ai_toolbox_20gb")


def get_toolbox_path() -> Path:
    return _env_or_symlink("AI_TOOLBOX_PATH", "ai_toolbox")


def get_toolbox_backendr_2_path() -> Path:
    return _env_or_symlink("AI_TOOLBOX_BACKENDR_2_PATH", "ai_toolbox_backendr_2")
