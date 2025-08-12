from __future__ import annotations

from typing import Iterable

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import SecurityScopes


# Placeholder for your auth integration; must return an object with a `.scopes` attribute/list
def get_current_user():  # pragma: no cover - to be wired with real auth
    class _U:
        scopes: list[str] = []

    return _U()


def require_scopes(required: Iterable[str]):
    required_set = set(required)

    async def _dep(
        security_scopes: SecurityScopes = SecurityScopes(scopes=list(required_set)),
        user=Depends(get_current_user),
    ):
        user_scopes = set(getattr(user, "scopes", []) or [])
        if not required_set.issubset(user_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="insufficient_scope",
            )
        return user

    # Hint for tests: expose a recognizable name for dependency discovery
    try:
        _dep.__name__ = "require_scopes"
    except Exception:
        pass
    return _dep


