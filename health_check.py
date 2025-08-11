#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def check_path(path_str: str):
    return {
        "path": path_str,
        "exists": os.path.exists(path_str),
        "is_dir": os.path.isdir(path_str),
    }


def try_import(module_name: str):
    try:
        __import__(module_name)
        return {"module": module_name, "ok": True}
    except Exception as e:
        return {"module": module_name, "ok": False, "error": str(e)}


def load_env(env_path: str) -> bool:
    if not os.path.exists(env_path):
        return False
    try:
        # Lazy import to avoid hard dependency when not installed
        import importlib

        dotenv = importlib.import_module("dotenv")
        load_dotenv = getattr(dotenv, "load_dotenv", None)
        if callable(load_dotenv):
            load_dotenv(env_path)
            return True
    except Exception:
        try:
            with open(env_path) as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        key, val = line.strip().split("=", 1)
                        os.environ[key] = val.strip().strip('"')
            return True
        except Exception:
            return False


def main():
    base_dir = Path(__file__).resolve().parent
    env_loaded = load_env(str(base_dir / ".env"))

    paths = {
        "AI_PROJECT_RESOURCE_DRIVE": os.getenv(
            "AI_PROJECT_RESOURCE_DRIVE", "/Users/x/Desktop/AI_PROJECT_RESOURCE_DRIVE"
        ),
        "AI_TOOLBOX_20GB_PATH": os.getenv(
            "AI_TOOLBOX_20GB_PATH", "/Users/x/Desktop/AI_Toolbox_20GB"
        ),
        "AI_TOOLBOX_PATH": os.getenv("AI_TOOLBOX_PATH", "/Users/x/Desktop/AI_TOOLBOX"),
        "AI_TOOLBOX_BACKENDR_2_PATH": os.getenv(
            "AI_TOOLBOX_BACKENDR_2_PATH", "/Users/x/Desktop/AI_TOOLBOX_BACKENDr 2"
        ),
    }

    path_checks = {key: check_path(val) for key, val in paths.items()}

    # Modules that should be present after safe install
    import_checks = [
        try_import(m)
        for m in [
            "pandas",  # from pandas
            "git",  # from GitPython
            "streamlit",  # from streamlit
            "dotenv",  # from python-dotenv
            "grok",  # likely missing (from grok-python)
        ]
    ]

    required_paths_ok = all(
        path_checks[k]["exists"] and path_checks[k]["is_dir"]
        for k in ["AI_PROJECT_RESOURCE_DRIVE", "AI_TOOLBOX_20GB_PATH", "AI_TOOLBOX_PATH"]
    )
    pandas_ok = any(ic["module"] == "pandas" and ic["ok"] for ic in import_checks)

    summary = {
        "env_loaded": env_loaded,
        "paths": path_checks,
        "imports": import_checks,
        "ok": bool(required_paths_ok and pandas_ok),
        "notes": [
            "sqlite3 is part of the Python standard library and not needed via pip.",
        ],
    }

    print(json.dumps(summary, indent=2))
    sys.exit(0 if summary["ok"] else 1)


if __name__ == "__main__":
    main()
