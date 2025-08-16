from __future__ import annotations

import contextlib
from collections.abc import Iterable

from app.security.jwt_hs256 import HS256JWT
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import SecurityScopes


# Placeholder for your auth integration; must return an object with a `.scopes` attribute/list
def get_current_user():  # pragma: no cover - default user object for tests
    class _U:
        scopes: list[str] = []

    return _U()


def _dynamic_user_dep():  # pragma: no cover - allows monkeypatch in tests
    # Import inside to resolve the latest function after monkeypatching
    from app.security import deps as security_deps

    # When not patched, fall back to a stub user with no scopes
    try:
        return security_deps.get_current_user()
    except Exception:
        class _U:
            scopes: list[str] = []

        return _U()


def require_scopes(required: Iterable[str]):
    required_set = set(required)

    async def _dep(
        security_scopes: SecurityScopes = SecurityScopes(scopes=list(required_set)),  # noqa: B008
        user=Depends(_dynamic_user_dep),  # noqa: B008
    ):
        user_scopes = set(getattr(user, "scopes", []) or [])
        if not required_set.issubset(user_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="insufficient_scope",
            )
        return user

    # Hint for tests: expose a recognizable name for dependency discovery
    with contextlib.suppress(AttributeError, TypeError):
        _dep.__name__ = "require_scopes"
    return _dep


async def verify_jwt_token(authorization: str = Header(None)) -> dict:
    """
    Verify JWT token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Decoded token claims

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use 'Bearer <token>'"
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is required"
        )

    try:
        # For now, use a default secret - in production this should come from environment
        jwt_handler = HS256JWT(secret="change-me")
        claims = jwt_handler.verify(token)
        return claims
    except (ValueError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        ) from e


