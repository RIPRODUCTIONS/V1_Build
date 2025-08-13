from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class PersonalConfig:
    twitter_enabled: bool
    twitter_bearer_token: str | None
    linkedin_enabled: bool
    linkedin_access_token: str | None


def _as_bool(value: str | None) -> bool:
    if not value:
        return False
    v = value.strip().lower()
    return v in {"1", "true", "yes", "on"}


def get_personal_config() -> PersonalConfig:
    return PersonalConfig(
        twitter_enabled=_as_bool(os.getenv("TWITTER_ENABLED")),
        twitter_bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
        linkedin_enabled=_as_bool(os.getenv("LINKEDIN_ENABLED")),
        linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
    )

