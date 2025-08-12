"""Canonical API scopes used for RBAC checks."""

READ_RUNS = "runs:read"
WRITE_RUNS = "runs:write"

# Tasks
READ_TASKS = "tasks:read"
WRITE_TASKS = "tasks:write"

# Users/admin
ADMIN_TASKS = "tasks:admin"
ADMIN_USERS = "users:admin"

# Special-case scope to mark public endpoints that still require explicit dependency wiring
AUTH_PUBLIC = "auth:public"

ALL_SCOPES = {
    READ_RUNS,
    WRITE_RUNS,
    READ_TASKS,
    WRITE_TASKS,
    ADMIN_TASKS,
    ADMIN_USERS,
    AUTH_PUBLIC,
}


