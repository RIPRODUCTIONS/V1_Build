#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

from app.core.config import get_settings
from app.security.jwt_hs256 import HS256JWT


def main() -> None:
    p = argparse.ArgumentParser(description="Mint a HS256 JWT for dev use")
    p.add_argument("subject", help="sub claim")
    p.add_argument("--ttl", type=int, default=3600, help="TTL seconds (default: 3600)")
    p.add_argument("--scopes", nargs="*", default=[], help="Optional scopes list")
    args = p.parse_args()

    settings = get_settings()
    secret = os.getenv("JWT_SECRET", settings.jwt_secret)
    helper = HS256JWT(secret=secret)
    token = helper.mint(subject=args.subject, scopes=args.scopes, ttl_override_seconds=args.ttl)
    print(json.dumps({"access_token": token}))


if __name__ == "__main__":
    main()
