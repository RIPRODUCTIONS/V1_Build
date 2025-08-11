from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Sequence

import jwt


class HS256JWT:
    """Lightweight HS256 JWT helper used for minting/verifying stateless tokens.

    This is additive and does not change the existing login flow. It can be used in
    tests or new dependencies without impacting current behavior.
    """

    def __init__(
        self,
        secret: str,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        ttl_seconds: int = 3600,
        leeway_seconds: int = 0,
    ) -> None:
        self.secret = secret
        self.issuer = issuer
        self.audience = audience
        self.ttl_seconds = ttl_seconds
        self.leeway_seconds = leeway_seconds

    def mint(
        self,
        subject: str,
        scopes: Optional[Sequence[str]] = None,
        ttl_override_seconds: Optional[int] = None,
        not_before_offset_seconds: int = 0,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        ttl = self.ttl_seconds if ttl_override_seconds is None else ttl_override_seconds
        payload: Dict[str, Any] = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "nbf": int((now + timedelta(seconds=not_before_offset_seconds)).timestamp()),
            "exp": int((now + timedelta(seconds=ttl)).timestamp()),
        }
        if self.issuer:
            payload["iss"] = self.issuer
        if self.audience:
            payload["aud"] = self.audience
        if scopes:
            payload["scopes"] = list(scopes)
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def verify(self, token: str) -> Dict[str, Any]:
        """Verify token and return claims.

        Raises PyJWT exceptions (ExpiredSignatureError, ImmatureSignatureError, InvalidTokenError, etc.)
        to allow callers to map them to HTTP errors as desired.
        """
        kwargs: Dict[str, Any] = {
            "key": self.secret,
            "algorithms": ["HS256"],
            "leeway": self.leeway_seconds,
        }
        if self.issuer:
            kwargs["issuer"] = self.issuer
        if self.audience:
            kwargs["audience"] = self.audience
        return jwt.decode(token, **kwargs)



