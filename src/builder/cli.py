from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

from .config import Settings, summarize


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="builder", description="Builder CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_health = sub.add_parser("health", help="Run environment and dependency checks")
    p_health.set_defaults(func=cmd_health)

    p_show = sub.add_parser("show-paths", help="Print resolved paths and validation status")
    p_show.set_defaults(func=cmd_show_paths)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
