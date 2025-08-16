"""
HS256 JWT Implementation

This module provides JWT token creation and verification using HS256 algorithm.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt


class HS256JWT:
    """HS256 JWT token handler for authentication."""

    def __init__(self, secret: str, ttl_seconds: int = 3600):
        """
        Initialize the JWT handler.

        Args:
            secret: Secret key for signing tokens
            ttl_seconds: Default time-to-live in seconds
        """
        self.secret = secret
        self.ttl_seconds = ttl_seconds
        self.algorithm = "HS256"

    def mint(
        self,
        subject: str,
        ttl_override_seconds: int | None = None,
        not_before_offset_seconds: int = 0,
        **additional_claims: Any
    ) -> str:
        """
        Create a new JWT token.

        Args:
            subject: Subject identifier (usually user ID)
            ttl_override_seconds: Override default TTL
            not_before_offset_seconds: Not-before offset in seconds
            **additional_claims: Additional claims to include

        Returns:
            JWT token string
        """
        now = datetime.now(UTC)
        ttl = ttl_override_seconds if ttl_override_seconds is not None else self.ttl_seconds

        payload = {
            "sub": subject,
            "iat": now,
            "exp": now + timedelta(seconds=ttl),
            "nbf": now + timedelta(seconds=not_before_offset_seconds),
            **additional_claims
        }

        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify(self, token: str) -> dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            jwt.InvalidTokenError: If token is invalid
            jwt.ExpiredSignatureError: If token has expired
            jwt.ImmatureSignatureError: If token is not yet valid
        """
        try:
            payload: dict[str, Any] = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise
        except jwt.ImmatureSignatureError:
            raise
        except jwt.InvalidTokenError:
            raise
        except Exception as e:
            raise jwt.InvalidTokenError(f"Token verification failed: {e}") from e

    def is_valid(self, token: str) -> bool:
        """
        Check if a token is valid without raising exceptions.

        Args:
            token: JWT token string

        Returns:
            True if token is valid, False otherwise
        """
        try:
            self.verify(token)
            return True
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.ImmatureSignatureError):
            return False
