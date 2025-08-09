from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

import builder.jobs.builtin  # noqa: F401 ensures builtin jobs are registered

from .config import Settings, summarize
from .jobs import get_job, list_jobs


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

    # cmd_scaffold removed (automation-only scope)
    # def cmd_scaffold(args: argparse.Namespace) -> int:
    settings = Settings.load()
    return 0


def cmd_jobs_list(_: argparse.Namespace) -> int:
    for name in list_jobs():
        print(name)
    return 0


def cmd_jobs_run(args: argparse.Namespace) -> int:
    job = get_job(args.name)
    if not job:
        print(f"Unknown job: {args.name}", flush=True)
        return 1
    return int(job())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="builder", description="Builder CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_health = sub.add_parser("health", help="Run environment and dependency checks")
    p_health.set_defaults(func=cmd_health)

    p_show = sub.add_parser("show-paths", help="Print resolved paths and validation status")
    p_show.set_defaults(func=cmd_show_paths)

    p_jobs = sub.add_parser("jobs", help="Job utilities")
    jobs_sub = p_jobs.add_subparsers(dest="jobs_cmd", required=True)
    p_jobs_list = jobs_sub.add_parser("list", help="List available jobs")
    p_jobs_list.set_defaults(func=cmd_jobs_list)
    p_jobs_run = jobs_sub.add_parser("run", help="Run a job by name")
    p_jobs_run.add_argument("name", help="Job name")
    p_jobs_run.set_defaults(func=cmd_jobs_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ret = args.func(args)
    return int(ret)


if __name__ == "__main__":
    raise SystemExit(main())
