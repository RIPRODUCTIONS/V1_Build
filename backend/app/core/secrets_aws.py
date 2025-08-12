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


