from __future__ import annotations

from collections import defaultdict

from app.security.rbac_map import RBAC_ROUTE_SCOPE_MAP


def test_rbac_map_has_no_overlapping_regexes_for_same_method():
    by_method: dict[str, list[tuple[str, set[str]]]] = defaultdict(list)
    for rx, method_map in RBAC_ROUTE_SCOPE_MAP:
        for method, scopes in method_map.items():
            by_method[method].append((rx.pattern, scopes))

    conflicts: list[tuple[str, str, set[str], set[str]]] = []
    for method, entries in by_method.items():
        seen: dict[str, set[str]] = {}
        for pattern, scopes in entries:
            if pattern in seen and seen[pattern] != scopes:
                conflicts.append((method, pattern, seen[pattern], scopes))
            seen[pattern] = scopes

    assert not conflicts, f"RBAC regex conflicts: {conflicts}"


