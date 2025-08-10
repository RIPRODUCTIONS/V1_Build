import os
import subprocess

from app.core.config import Settings


def resolve_secret(key: str, idx: dict[str, dict[str, str]], s: Settings) -> str | None:
    meta = idx.get(key)
    if not meta:
        return os.getenv(key)
    provider = meta.get("provider", "env")
    ref = meta.get("ref", "")
    if provider == "env":
        return os.getenv(ref or key)
    if provider == "1password":
        try:
            return subprocess.check_output([s.OP_CLI, "read", ref], text=True).strip()
        except Exception:
            return None
    if provider == "notion_inline":
        return ref or None
    return None
