from __future__ import annotations

import asyncio
import os
from typing import Any

from core.db import save_finding


class KaliSecurityAdapter:
    """Lightweight adapter to run common scans via local tools or Kali container.
    Controlled by ENABLE_KALI_INTEGRATION feature flag.
    """

    def __init__(self) -> None:
        self.enabled = os.environ.get("ENABLE_KALI_INTEGRATION", "0") == "1"
        self.use_container = os.environ.get("USE_KALI_CONTAINER", "0") == "1"
        self.compose_file = os.environ.get("KALI_COMPOSE_FILE", "docker-compose.kali.yml")

    async def run(self, cmd: list[str]) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await proc.communicate()
        code = 0 if proc.returncode is None else int(proc.returncode)
        return code, out.decode(), err.decode()

    async def nmap_scan(self, target: str, args: list[str] | None = None) -> dict[str, Any]:
        base = ["nmap", "-sV", "-T4", target]
        if args:
            base.extend(args)
        if self.use_container:
            cmd = ["docker-compose", "-f", self.compose_file, "run", "--rm", "kali"] + base
        else:
            cmd = base
        code, out, err = await self.run(cmd)
        save_finding(source="nmap", target=target, title="nmap_scan", severity="info", description=err if err else None, data={"output": out})
        return {"code": code, "stdout": out, "stderr": err}

    async def nikto_scan(self, target: str) -> dict[str, Any]:
        base = ["nikto", "-h", target, "-ask", "no"]
        cmd = (["docker-compose", "-f", self.compose_file, "run", "--rm", "kali"] + base) if self.use_container else base
        code, out, err = await self.run(cmd)
        save_finding(source="nikto", target=target, title="nikto_scan", severity="info", description=err if err else None, data={"output": out})
        return {"code": code, "stdout": out, "stderr": err}

    async def zap_spider(self, target: str) -> dict[str, Any]:
        # Quick spider using ZAP baseline container if available
        base = ["zap-baseline.py", "-t", target, "-I", "-r", "zap_report.html"]
        cmd = (["docker-compose", "-f", self.compose_file, "run", "--rm", "kali"] + base) if self.use_container else base
        code, out, err = await self.run(cmd)
        save_finding(source="zap", target=target, title="zap_spider", severity="info", description=err if err else None, data={"output": out})
        return {"code": code, "stdout": out, "stderr": err}

    async def sqlmap_test(self, target_url: str, params: list[str] | None = None) -> dict[str, Any]:
        base = ["sqlmap", "-u", target_url, "--batch", "--level", "2"]
        if params:
            for p in params:
                base += ["-p", p]
        cmd = (["docker-compose", "-f", self.compose_file, "run", "--rm", "kali"] + base) if self.use_container else base
        code, out, err = await self.run(cmd)
        severity = "high" if "sql injection" in out.lower() else "info"
        save_finding(source="sqlmap", target=target_url, title="sqlmap_result", severity=severity, description=err if err else None, data={"output": out})
        return {"code": code, "stdout": out, "stderr": err}





