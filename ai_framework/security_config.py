#!/usr/bin/env python3
"""Production Security Configuration."""

from __future__ import annotations

import os
import secrets
from contextlib import suppress
from pathlib import Path


class SecurityConfig:
    MASTER_API_KEY = os.getenv("MASTER_API_KEY", f"master-{secrets.token_urlsafe(32)}")
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", f"admin-{secrets.token_urlsafe(32)}")
    USER_API_KEY = os.getenv("USER_API_KEY", f"user-{secrets.token_urlsafe(32)}")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(64))
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

    ALLOWED_ORIGINS = (
        os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
    )
    SSL_REQUIRED = os.getenv("SSL_REQUIRED", "false").lower() == "true"

    @classmethod
    def save_keys_to_file(cls) -> Path:
        keys_file = Path.home() / ".ai_framework_keys"
        keys_file.write_text(
            "\n".join(
                [
                    f"MASTER_API_KEY={cls.MASTER_API_KEY}",
                    f"ADMIN_API_KEY={cls.ADMIN_API_KEY}",
                    f"USER_API_KEY={cls.USER_API_KEY}",
                    f"JWT_SECRET_KEY={cls.JWT_SECRET_KEY}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        with suppress(Exception):
            os.chmod(keys_file, 0o600)
        print(f"Security keys saved to: {keys_file}")
        return keys_file


if __name__ == "__main__":
    SecurityConfig.save_keys_to_file()




