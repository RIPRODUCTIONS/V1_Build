from __future__ import annotations

import re
from typing import Iterable

from .scopes import (
    ADMIN_TASKS,
    ADMIN_USERS,
    READ_RUNS,
    WRITE_RUNS,
    READ_TASKS,
    WRITE_TASKS,
)


# Path regexes map to required scopes by HTTP method
RBAC_ROUTE_SCOPE_MAP: list[tuple[re.Pattern[str], dict[str, set[str]]]] = [
    # Runs slice (API routes)
    (re.compile(r"^/api/runs$"), {
        "GET": {READ_RUNS},
        "POST": {WRITE_RUNS},
    }),
    (re.compile(r"^/api/runs/\d+$"), {
        "GET": {READ_RUNS},
        "PATCH": {WRITE_RUNS},
        "PUT": {WRITE_RUNS},
        "DELETE": {WRITE_RUNS},
    }),

    # Tasks/agent admin (example)
    (re.compile(r"^/admin/cleanup/.*$"), {
        "DELETE": {ADMIN_TASKS},
    }),

    # Tasks (CRUD)
    (re.compile(r"^/tasks$"), {
        "GET": {READ_TASKS},
        "POST": {WRITE_TASKS},
    }),
    (re.compile(r"^/tasks/\\d+$"), {
        "GET": {READ_TASKS},
        "PUT": {WRITE_TASKS},
        "PATCH": {WRITE_TASKS},
        "DELETE": {WRITE_TASKS},
    }),

    # Users/admin: protect explicit admin endpoints; login remains outside RBAC map
    (re.compile(r"^/users/me$"), {
        "GET": {ADMIN_USERS},
    }),
    (re.compile(r"^/users/register$"), {
        "POST": {ADMIN_USERS},
    }),
]

SAFE_METHODS: set[str] = {"GET", "HEAD", "OPTIONS"}


