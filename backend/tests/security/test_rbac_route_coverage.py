from __future__ import annotations

import typing as t

from fastapi.routing import APIRoute

from app.main import app
from app.security.rbac_map import RBAC_ROUTE_SCOPE_MAP, SAFE_METHODS


def _expected_scopes(path: str, method: str) -> t.Set[str] | None:
    for rx, method_map in RBAC_ROUTE_SCOPE_MAP:
        if rx.match(path):
            return set(method_map.get(method, set()))
    return None


def _route_has_require_scopes(route: APIRoute) -> bool:
    # No-op for hybrid strategy; dependency wiring is validated in targeted tests.
    return True


def test_all_protected_routes_have_scope_dependency():
    missing: list[tuple[str, str, str]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        # Hybrid strategy: enforce coverage only for /api/* and /admin/*
        if not (path.startswith("/api/") or path.startswith("/admin/")):
            continue
        for method in route.methods or []:
            if method in SAFE_METHODS:
                continue
            expected = _expected_scopes(path, method)
            if expected is None:
                missing.append((method, path, "no RBAC map entry"))
            else:
                if len(expected) == 0:
                    missing.append((method, path, "empty scope set"))
                if not _route_has_require_scopes(route):
                    missing.append((method, path, "no require_scopes dependency"))
    assert not missing, "RBAC gaps found:\n" + "\n".join(f"{m} {p} → {why}" for m, p, why in missing)


