from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import jwt

from app.core.config import get_settings


class JWTDecodeResult:
    def __init__(self, claims: dict[str, Any]):
        self.claims = claims

    @property
    def subject(self) -> str | None:
        sub = self.claims.get('sub')
        if isinstance(sub, str) and sub.strip():
            return sub
        return None


def decode_hs256_token(token: str) -> JWTDecodeResult:
    settings = get_settings()
    options = {
        'verify_signature': True,
        'verify_exp': settings.jwt_verify_exp,
        'verify_iat': settings.jwt_verify_iat,
        'verify_nbf': settings.jwt_verify_nbf,
        'require': [],
    }
    kwargs: dict[str, Any] = {
        'key': settings.jwt_secret,
        'algorithms': [settings.jwt_algorithm],
        'options': options,
        'leeway': settings.jwt_leeway_seconds or 0,
    }
    if settings.jwt_issuer:
        kwargs['issuer'] = settings.jwt_issuer
    if settings.jwt_audience:
        kwargs['audience'] = settings.jwt_audience

    claims = jwt.decode(token, **kwargs)
    iat = claims.get('iat')
    if (
        settings.jwt_verify_iat
        and isinstance(iat, (int | float))
        and (datetime.fromtimestamp(iat, tz=UTC) > datetime.now(UTC))
    ):
        raise jwt.ImmatureSignatureError('token not active yet (iat in future)')
    return JWTDecodeResult(claims)
