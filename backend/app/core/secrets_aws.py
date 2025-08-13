from __future__ import annotations

import json
import os
from typing import Any, Dict


def _merge_env_from_secret(secret_blob: str) -> None:
    try:
        data: Dict[str, Any] = json.loads(secret_blob)
    except json.JSONDecodeError:
        # Support KEY=VAL\n format
        for line in secret_blob.splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
        return
    for k, v in data.items():
        if isinstance(v, (str, int, float)):
            os.environ.setdefault(str(k), str(v))


def maybe_load_from_aws() -> None:
    """Load secrets from AWS Secrets Manager if configured.

    Controlled by env:
      - ENV=production|prod (only then)
      - AWS_REGION
      - AWS_SECRETS_NAME (name of secret containing a JSON or KEY=VAL file)
    """
    env = os.getenv("ENV", "").lower()
    if env not in {"production", "prod"}:
        return
    name = os.getenv("AWS_SECRETS_NAME")
    region = os.getenv("AWS_REGION")
    if not name or not region:
        return
    try:  # pragma: no cover - optional dependency
        import boto3  # type: ignore

        client = boto3.client("secretsmanager", region_name=region)
        resp = client.get_secret_value(SecretId=name)
        blob = resp.get("SecretString")
        if blob:
            _merge_env_from_secret(blob)
    except Exception:
        # Never crash app start if AWS is unavailable; fail-closed
        return

from __future__ import annotations

import json
import os
from typing import Any, Dict


def maybe_load_from_aws() -> None:
    """If running in production and AWS_SECRETS_NAME is set, fetch JSON and merge into env.

    Expected JSON: { "JWT_SECRET": "...", ... }
    Existing env vars take precedence.
    """
    env = os.getenv("ENV", "").lower()
    name = os.getenv("AWS_SECRETS_NAME")
    if env not in {"production", "prod"} or not name:
        return

    try:
        import boto3  # type: ignore

        client = boto3.client("secretsmanager")
        resp: Dict[str, Any] = client.get_secret_value(SecretId=name)
        secret_str = resp.get("SecretString")
        if not secret_str:
            return
        data = json.loads(secret_str)
        if not isinstance(data, dict):
            return
        for k, v in data.items():
            if k and isinstance(k, str) and k not in os.environ and isinstance(v, str):
                os.environ[k] = v
    except Exception:
        # Do not crash on missing AWS creds; fail-fast will still enforce required keys later.
        return


