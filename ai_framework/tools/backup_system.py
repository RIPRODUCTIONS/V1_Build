from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
from pathlib import Path


class AutoBackupSystem:
    def __init__(self, root: Path, out_dir: Path | None = None) -> None:
        self.root = root
        self.out = out_dir or (root / "backups")
        self.out.mkdir(parents=True, exist_ok=True)

    def _ts(self) -> str:
        return dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    def backup_sqlite(self, db_url: str) -> Path | None:
        # Only supports sqlite path format sqlite:///file
        if not db_url.startswith("sqlite:///"):
            return None
        db_path = Path(db_url.replace("sqlite:///", ""))
        if not db_path.exists():
            return None
        dest = self.out / f"sqlite-{self._ts()}.db"
        shutil.copy2(db_path, dest)
        return dest

    def compress_logs(self) -> Path:
        # fallback for generic logs directory
        target = self.out / f"logs-{self._ts()}.tar.gz"
        subprocess.call(["tar", "-czf", str(target), "logs"], cwd=str(self.root))
        return target

    def run_nightly(self) -> list[Path]:
        artifacts: list[Path] = []
        db_url = os.environ.get("DB_URL", "sqlite:///ai_framework.db")
        p = self.backup_sqlite(db_url)
        if p:
            artifacts.append(p)
        artifacts.append(self.compress_logs())
        # TODO: optional S3 sync if configured
        return artifacts


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    b = AutoBackupSystem(root)
    arts = b.run_nightly()
    for a in arts:
        print("backup:", a)







