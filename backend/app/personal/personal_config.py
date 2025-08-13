from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class PersonalConfig:
    twitter_enabled: bool
    twitter_bearer_token: str | None
    twitter_api_base: str | None
    twitter_user_token: str | None
    linkedin_enabled: bool
    linkedin_access_token: str | None
    linkedin_member_urn: str | None
    post_real_enabled: bool
    twitter_client_id: str | None
    twitter_client_secret: str | None
    twitter_redirect_uri: str | None
    linkedin_client_id: str | None
    linkedin_client_secret: str | None
    linkedin_redirect_uri: str | None
    oauth_exchange_real: bool


def _as_bool(value: str | None) -> bool:
    if not value:
        return False
    v = value.strip().lower()
    return v in {"1", "true", "yes", "on"}


def get_personal_config() -> PersonalConfig:
    return PersonalConfig(
        twitter_enabled=_as_bool(os.getenv("TWITTER_ENABLED")),
        twitter_bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
        twitter_api_base=os.getenv("TWITTER_API_BASE", "https://api.twitter.com"),
        twitter_user_token=os.getenv("TWITTER_USER_TOKEN"),
        linkedin_enabled=_as_bool(os.getenv("LINKEDIN_ENABLED")),
        linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
        linkedin_member_urn=os.getenv("LINKEDIN_MEMBER_URN"),
        post_real_enabled=_as_bool(os.getenv("SOCIAL_POST_REAL")),
        twitter_client_id=os.getenv("TWITTER_CLIENT_ID"),
        twitter_client_secret=os.getenv("TWITTER_CLIENT_SECRET"),
        twitter_redirect_uri=os.getenv("TWITTER_REDIRECT_URI"),
        linkedin_client_id=os.getenv("LINKEDIN_CLIENT_ID"),
        linkedin_client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
        linkedin_redirect_uri=os.getenv("LINKEDIN_REDIRECT_URI"),
        oauth_exchange_real=_as_bool(os.getenv("SOCIAL_OAUTH_EXCHANGE_REAL")),
    )

