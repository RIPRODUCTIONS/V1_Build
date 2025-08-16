#!/usr/bin/env python3
"""
Desktop signing/notarization integration.

Runs the macOS signing pipeline script with environment variables for identity and notarization.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], env: dict[str, str]) -> int:
    print("[sign] $", " ".join(cmd))
    proc = subprocess.Popen(cmd, env=env)
    return proc.wait()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    desktop_dir = repo_root / "apps" / "desktop"
    script = desktop_dir / "scripts" / "sign_and_notarize.sh"

    if not script.exists():
        print(f"[sign:ERROR] script not found: {script}", file=sys.stderr)
        return 1

    identity = os.environ.get("IDENTITY") or os.environ.get("CSC_NAME")
    team_id = os.environ.get("TEAM_ID") or os.environ.get("APPLE_TEAM_ID")
    apple_id = os.environ.get("APPLE_ID")
    app_password = os.environ.get("APP_PASSWORD")
    notary_profile = os.environ.get("NOTARY_PROFILE")
    app_name = os.environ.get("APP_NAME", "Atomic Desktop.app")

    if not identity or not team_id:
        print("[sign:ERROR] IDENTITY and TEAM_ID are required", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env.update({
        "IDENTITY": identity,
        "TEAM_ID": team_id,
        "APP_NAME": app_name,
    })
    if apple_id:
        env["APPLE_ID"] = apple_id
    if app_password:
        env["APP_PASSWORD"] = app_password
    if notary_profile:
        env["NOTARY_PROFILE"] = notary_profile

    # Ensure dist exists by building unsigned if needed
    build_cmd = ["bash", "-lc", f"cd \"{desktop_dir}\" && CSC_IDENTITY_AUTO_DISCOVERY=false npx --yes electron-builder --mac --dir"]
    if run(build_cmd, env) != 0:
        print("[sign:ERROR] unsigned build failed", file=sys.stderr)
        return 3

    # Run sign + notarize
    cmd = ["bash", str(script)]
    code = run(cmd, env)
    if code != 0:
        print(f"[sign:ERROR] signing pipeline failed with exit {code}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())







