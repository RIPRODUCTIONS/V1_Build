from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

from .config import Settings, summarize
from .scaffold import ScaffoldOptions, scaffold_project


def _try_import(module_name: str) -> dict[str, Any]:
    try:
        importlib.import_module(module_name)
        return {"module": module_name, "ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"module": module_name, "ok": False, "error": str(exc)}


def cmd_health(_: argparse.Namespace) -> int:
    settings = Settings.load()
    issues = settings.validate()

    imports = [
        _try_import("pandas"),
        _try_import("git"),
        _try_import("streamlit"),
        _try_import("dotenv"),
        _try_import("grok"),  # optional; generally missing unless provided
    ]

    ok = len(issues) == 0 and any(i["module"] == "pandas" and i["ok"] for i in imports)

    result: dict[str, Any] = {
        "settings": summarize(settings),
        "imports": imports,
        "ok": bool(ok),
    }
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


def cmd_show_paths(_: argparse.Namespace) -> int:
    settings = Settings.load()
    print(json.dumps(summarize(settings), indent=2))
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    settings = Settings.load()
    out = scaffold_project(
        settings.workspace_dir, ScaffoldOptions(project_name=args.name, force=bool(args.force))
    )
    print(str(out))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="builder", description="Builder CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_health = sub.add_parser("health", help="Run environment and dependency checks")
    p_health.set_defaults(func=cmd_health)

    p_show = sub.add_parser("show-paths", help="Print resolved paths and validation status")
    p_show.set_defaults(func=cmd_show_paths)

    p_scaf = sub.add_parser(
        "scaffold", help="Generate a new project skeleton under projects/<name>"
    )
    p_scaf.add_argument("name", help="Project name (directory under projects/)")
    p_scaf.add_argument("--force", action="store_true", help="Overwrite existing files if present")
    p_scaf.set_defaults(func=cmd_scaffold)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ret = args.func(args)
    return int(ret)


if __name__ == "__main__":
    raise SystemExit(main())
