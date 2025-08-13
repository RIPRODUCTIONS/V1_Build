from __future__ import annotations

from typing import Iterable

from fastapi import Depends, HTTPException, Security, status
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
        return security_deps.get_current_user()  # type: ignore[attr-defined]
    except Exception:
        class _U:
            scopes: list[str] = []

        return _U()


def require_scopes(required: Iterable[str]):
    required_set = set(required)

    async def _dep(
        security_scopes: SecurityScopes = SecurityScopes(scopes=list(required_set)),
        user=Depends(_dynamic_user_dep),
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


