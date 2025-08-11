from __future__ import annotations

import jwt
from app.core.config import get_settings
from app.security.jwt_hs256 import HS256JWT


def test_hs256_mint_and_verify_subject_ok() -> None:
    settings = get_settings()
    helper = HS256JWT(secret=settings.jwt_secret)
    token = helper.mint(subject="user-123", ttl_override_seconds=60)
    claims = helper.verify(token)
    assert claims.get("sub") == "user-123"


def test_hs256_verify_expired_raises() -> None:
    settings = get_settings()
    helper = HS256JWT(secret=settings.jwt_secret, ttl_seconds=1)
    token = helper.mint(subject="user-expired", ttl_override_seconds=0)
    # Ensure exp in the past
    with __import__("pytest").raises(jwt.ExpiredSignatureError):
        helper.verify(token)


def test_hs256_verify_not_active_raises() -> None:
    settings = get_settings()
    helper = HS256JWT(secret=settings.jwt_secret)
    # nbf in future
    token = helper.mint(subject="user-nbf", ttl_override_seconds=60, not_before_offset_seconds=30)
    with __import__("pytest").raises(jwt.ImmatureSignatureError):
        helper.verify(token)


def test_hs256_verify_invalid_signature_raises() -> None:
    settings = get_settings()
    bad_secret = settings.jwt_secret + "-wrong"
    helper = HS256JWT(secret=bad_secret)
    token = helper.mint(subject="user-bad", ttl_override_seconds=60)
    good = HS256JWT(secret=settings.jwt_secret)
    with __import__("pytest").raises(jwt.InvalidTokenError):
        good.verify(token)
