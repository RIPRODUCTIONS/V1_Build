from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect

from core.db import DB_URL, TaskRecord, get_session


@dataclass
class DiagnosticReport:
    timestamp: str
    architecture: dict[str, Any]
    connectivity: dict[str, Any]
    agents: dict[str, Any]
    database: dict[str, Any]
    api_wiring: dict[str, Any]
    apps: dict[str, Any]
    files: dict[str, Any]
    health: dict[str, Any]
    mermaid_diagram: str


class SystemDiagnostics:
    def __init__(self) -> None:
        self.timestamp = datetime.now(UTC).isoformat()

    async def generate_report(self, server) -> DiagnosticReport:
        arch = await self._map_architecture(server)
        conn = await self._analyze_connectivity(server)
        agents = await self._inspect_agents(server)
        db = await self._inspect_database()
        api = await self._verify_api_wiring(server)
        apps = await self._inspect_apps()
        files = await self._project_tree()
        health = await self._assess_health({"arch": arch, "agents": agents, "apps": apps})
        diagram = self._build_mermaid_diagram(arch)
        return DiagnosticReport(
            timestamp=self.timestamp,
            architecture=arch,
            connectivity=conn,
            agents=agents,
            database=db,
            api_wiring=api,
            apps=apps,
            files=files,
            health=health,
            mermaid_diagram=diagram,
        )

    async def _map_architecture(self, server) -> dict[str, Any]:
        components: dict[str, Any] = {
            "fastapi": True,
            "redis": bool(os.getenv("REDIS_URL")),
            "db_url": DB_URL,
            "scheduler_enabled": os.getenv("ENABLE_SCHEDULER") == "1",
            "alerts_enabled": os.getenv("ENABLE_ALERTS", "1") == "1",
            "scale700_enabled": os.getenv("ENABLE_SCALE700") == "1",
            "browser_operator_enabled": os.getenv("ENABLE_BROWSER_OPERATOR") == "1",
            "kali_enabled": os.getenv("ENABLE_KALI_INTEGRATION") == "1",
        }
        return {"components": components}

    async def _analyze_connectivity(self, server) -> dict[str, Any]:
        results: dict[str, Any] = {
            "websocket_clients": len(getattr(server, "ws_connections", []) or []),
            "redis_queue": bool(getattr(server, "scale_queue_manager", None) or getattr(server, "simple_scale700", None)),
            "scheduler_running": bool(server.scheduler),
        }
        return results

    async def _inspect_agents(self, server) -> dict[str, Any]:
        data: dict[str, Any] = {"total": 0, "active": 0, "agents": {}}
        dashboard = getattr(server, "dashboard", None)
        if not dashboard:
            return data
        agents = dashboard.agent_registry
        data["total"] = len(agents)
        active = 0
        for aid, agent in agents.items():
            status = getattr(agent, "status", None)
            svalue = getattr(status, "value", str(status)) if status else "unknown"
            if svalue in ("idle", "running", "ready"):
                active += 1
            capabilities = []
            try:
                caps = getattr(agent.config, "capabilities", None)
                if caps:
                    capabilities = [str(c) for c in caps]
            except Exception:
                capabilities = []
            data["agents"][aid] = {
                "name": agent.config.name,
                "department": getattr(agent.config.department, "value", str(agent.config.department)),
                "status": svalue,
                "capabilities": capabilities,
            }
        data["active"] = active
        return data

    async def _inspect_database(self) -> dict[str, Any]:
        engine = create_engine(DB_URL, future=True)
        insp = inspect(engine)
        tables = insp.get_table_names()
        schema: dict[str, Any] = {}
        counts: dict[str, int] = {}
        relations: dict[str, list[dict[str, Any]]] = {}
        for t in tables:
            cols = []
            for c in insp.get_columns(t):
                cols.append({"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)})
            fks = []
            for fk in insp.get_foreign_keys(t):
                fks.append({
                    "constrained_columns": fk.get("constrained_columns", []),
                    "referred_table": fk.get("referred_table"),
                    "referred_columns": fk.get("referred_columns", []),
                })
            relations[t] = fks
            schema[t] = cols
            try:
                with engine.connect() as conn:
                    res = conn.execute(f"SELECT COUNT(*) FROM {t}")
                    counts[t] = int(list(res)[0][0])
            except Exception:
                counts[t] = 0
        # Top N recent tasks
        recent: list[dict[str, Any]] = []
        try:
            with get_session() as session:
                q = (
                    session.query(TaskRecord)
                    .order_by(TaskRecord.created_at.desc())
                    .limit(10)
                    .all()
                )
                for r in q:
                    recent.append(
                        {
                            "task_id": r.task_id,
                            "agent_id": r.agent_id,
                            "status": r.status,
                            "created_at": r.created_at.isoformat() if r.created_at else None,
                        }
                    )
        except Exception:
            pass
        return {
            "engine": DB_URL.split(":", 1)[0],
            "tables": tables,
            "schema": schema,
            "relations": relations,
            "counts": counts,
            "recent_tasks": recent,
        }

    async def _verify_api_wiring(self, server) -> dict[str, Any]:
        app = server.app
        endpoints: list[dict[str, Any]] = []
        if app:
            for r in app.router.routes:
                try:
                    path = getattr(r, "path", "")
                    methods = list(getattr(r, "methods", []) or [])
                    name = getattr(r, "name", "")
                    auth_required = bool(getattr(r, "dependencies", None))
                    endpoints.append({
                        "path": path,
                        "methods": methods,
                        "name": name,
                        "auth_required": auth_required,
                    })
                except Exception:
                    continue
        missing_critical = [p for p in ["/health", "/ready", "/metrics/system"] if p not in [e["path"] for e in endpoints]]
        return {"endpoints": endpoints, "missing": missing_critical}

    async def _inspect_apps(self) -> dict[str, Any]:
        root = Path(__file__).resolve().parents[1]
        apps_dir = root.parent / "apps"
        status: dict[str, Any] = {"web": {}, "mobile": {}, "desktop": {}}
        # Web
        web_dir = apps_dir / "web"
        status["web"]["present"] = web_dir.exists()
        api_base = None
        try:
            api_file = web_dir / "src" / "lib" / "api.ts"
            if api_file.exists():
                content = api_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if "API_BASE" in line and "http" in line:
                        api_base = line.strip()
                        break
        except Exception:
            pass
        status["web"]["api_config_line"] = api_base
        # Mobile
        mobile_dir = apps_dir / "mobile"
        status["mobile"]["present"] = mobile_dir.exists()
        svc = mobile_dir / "src" / "services" / "EnterpriseAPIService.ts"
        status["mobile"]["service_present"] = svc.exists()
        # Desktop
        desktop_dir = apps_dir / "desktop"
        status["desktop"]["present"] = desktop_dir.exists()
        main_js = desktop_dir / "main.js"
        status["desktop"]["main_present"] = main_js.exists()
        return status

    async def _project_tree(self, max_depth: int = 3) -> dict[str, Any]:
        root = Path(__file__).resolve().parents[2]
        tree: dict[str, Any] = {}

        def add_dir(p: Path, depth: int) -> Any:
            if depth > max_depth:
                return "…"
            entry: dict[str, Any] = {}
            try:
                for child in sorted(p.iterdir()):
                    name = child.name
                    if child.is_dir():
                        entry[name] = add_dir(child, depth + 1)
                    elif depth <= max_depth - 1:
                        entry.setdefault("__files__", []).append(name)
            except Exception:
                return entry
            return entry

        for top in ["ai_framework", "apps", "backend", "autonomous_system", "scripts", "src"]:
            p = root / top
            if p.exists():
                tree[top] = add_dir(p, 1)
        return tree

    async def _assess_health(self, health_data: dict[str, Any]) -> dict[str, Any]:
        """Assess system health using a dictionary to reduce parameter count."""
        # Extract parameters from dictionary
        arch = health_data.get("arch", {})
        agents = health_data.get("agents", {})
        apps = health_data.get("apps", {})

        issues: list[str] = []
        if not arch.get("components", {}).get("db_url"):
            issues.append("No DB_URL configured")
        if agents.get("total", 0) == 0:
            issues.append("No agents loaded")
        if not apps.get("web", {}).get("present"):
            issues.append("Web app not detected")
        ok = len(issues) == 0
        return {"ok": ok, "issues": issues}

    def _build_mermaid_diagram(self, arch) -> str:
        has_redis = arch["components"].get("redis", False)
        lines = [
            "graph TD",
            "  subgraph Backend",
            "    A[FastAPI Server]",
            "    B[Agent Orchestrator]",
            "    C[Master Dashboard]",
            "    S[Scheduler]",
            "    M[Metrics Collector]",
            "    AL[Alert Manager]",
            "  end",
            "  D[(Database)]",
            "  E[/Redis/]",
        ]
        if arch["components"].get("browser_operator_enabled"):
            lines.append("  BO[[Browser Operator]]")
        if arch["components"].get("kali_enabled"):
            lines.append("  KA[[Kali Adapter]]")
        lines += [
            "  A --> B",
            "  B --> C",
            "  A --> D",
            "  A --> S",
            "  A --> M",
            "  A --> AL",
        ]
        if has_redis:
            lines.append("  A --> E")
        if arch["components"].get("browser_operator_enabled"):
            lines.append("  A -.-> BO")
        if arch["components"].get("kali_enabled"):
            lines.append("  A -.-> KA")
        return "\n".join(lines)


async def run_diagnostics(server) -> dict[str, Any]:
    diag = SystemDiagnostics()
    rep = await diag.generate_report(server)
    return {
        "timestamp": rep.timestamp,
        "architecture": rep.architecture,
        "connectivity": rep.connectivity,
        "agents": rep.agents,
        "database": rep.database,
        "api_wiring": rep.api_wiring,
        "apps": rep.apps,
        "files": rep.files,
        "health": rep.health,
        "mermaid": rep.mermaid_diagram,
    }


def report_to_markdown(rep: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"## System Report ({rep.get('timestamp')})")
    # Agents
    ag = rep.get("agents", {})
    lines.append("\n### Agents")
    lines.append(f"Total: {ag.get('total', 0)} Active: {ag.get('active', 0)}")
    for aid, ainfo in (ag.get("agents", {}) or {}).items():
        caps = ", ".join(ainfo.get("capabilities", []) or [])
        lines.append(f"- {aid}: {ainfo.get('name')} [{ainfo.get('department')}] status={ainfo.get('status')} caps=[{caps}]")
    # Database
    db = rep.get("database", {})
    lines.append("\n### Database")
    lines.append(f"Engine: {db.get('engine')}")
    for t in db.get("tables", []):
        cnt = db.get("counts", {}).get(t, 0)
        lines.append(f"- {t} (rows: {cnt})")
        for col in (db.get("schema", {}).get(t, []) or [])[:10]:
            lines.append(f"  - {col['name']}: {col['type']} {'NULL' if col.get('nullable') else 'NOT NULL'}")
    # API
    api = rep.get("api_wiring", {})
    lines.append("\n### API Endpoints")
    for ep in api.get("endpoints", [])[:200]:
        methods = ",".join(sorted(ep.get("methods", []) or []))
        lines.append(f"- {methods} {ep.get('path')} auth={ep.get('auth_required')}")
    # Apps
    lines.append("\n### Apps")
    for app_name, info in rep.get("apps", {}).items():
        lines.append(f"- {app_name}: {info}")
    # Architecture
    lines.append("\n### Architecture Diagram (Mermaid)")
    lines.append("```\n" + rep.get("mermaid", "") + "\n```")
    # Health
    health = rep.get("health", {})
    lines.append("\n### Health")
    lines.append(f"OK: {health.get('ok')} Issues: {', '.join(health.get('issues', []))}")
    # Files
    lines.append("\n### Files (top-level tree)")
    lines.append("```json\n" + str(rep.get("files", {})) + "\n```")
    return "\n".join(lines)


