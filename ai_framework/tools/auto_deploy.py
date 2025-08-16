from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print("[deploy] $", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(cwd) if cwd else None)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    # Pull latest changes
    if run(["git", "fetch", "--all"], repo_root) != 0:
        return 1
    if run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_root) != 0:
        return 1
    if run(["git", "pull", "--rebase"], repo_root) != 0:
        return 1
    # Install deps and migrate DB
    srv = repo_root / "ai_framework"
    venv = srv / ".venv"
    py = str(venv / "bin" / "python") if (venv / "bin" / "python").exists() else sys.executable
    run([py, "-m", "pip", "install", "-r", str(srv / "requirements.txt")])
    run([py, "-c", "from core.db import init_db; init_db(); print('DB migrated')"], srv)
    # Restart server
    run(["bash", "-lc", "cd ai_framework && pkill -f server.py || true && nohup python3 server.py > server.out 2>&1 &"], repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())







