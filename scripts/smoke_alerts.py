#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from urllib import request, parse


def load_env_from_file(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k and v and not os.environ.get(k):
                        os.environ[k] = v
    except FileNotFoundError:
        pass


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_env_from_file(os.path.join(root, ".env"))

    base = os.environ.get("API_URL", "http://127.0.0.1:8000")
    key = os.environ.get("INTERNAL_API_KEY", "")
    msg = os.environ.get("ALERT_MESSAGE", "Synthetic alert from smoke_alerts.py")

    url = f"{base}/alerts/test"

    payload = {"message": f"{msg} @ {time.strftime('%Y-%m-%d %H:%M:%S')}"}
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-API-Key"] = key
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            sys.stdout.write(body + "\n")
            return 0
    except Exception as e:
        sys.stdout.write(json.dumps({"error": str(e)}) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


