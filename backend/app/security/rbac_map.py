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
    READ_LEADS,
    WRITE_AI,
)


# Path regexes map to required scopes by HTTP method
RBAC_ROUTE_SCOPE_MAP: list[tuple[re.Pattern[str], dict[str, set[str]]]] = [
    # Runs slice (API routes)
    (re.compile(r"^/api/runs$"), {
        "GET": {READ_RUNS},
        "POST": {WRITE_RUNS},
    }),
    # Match FastAPI route literal with param token
    (re.compile(r"^/api/runs/\{run_id\}$"), {
        "GET": {READ_RUNS},
        "PATCH": {WRITE_RUNS},
        "PUT": {WRITE_RUNS},
        "DELETE": {WRITE_RUNS},
    }),

    # Admin cleanup endpoints
    (re.compile(r"^/admin/cleanup/leads$"), {"DELETE": {ADMIN_TASKS}}),
    (re.compile(r"^/admin/cleanup/tasks$"), {"DELETE": {ADMIN_TASKS}}),
    (re.compile(r"^/admin/cleanup/all$"), {"DELETE": {ADMIN_TASKS}}),
    # Admin integrations/dev tooling
    (re.compile(r"^/admin/integrations/google/oauth/\{user_id\}$"), {"POST": {ADMIN_TASKS}}),
    (re.compile(r"^/admin/automations/seed_calendar_rules$"), {"POST": {ADMIN_TASKS}}),
    (re.compile(r"^/admin/dlq/\{queue\}/replay/\{item_id\}$"), {"POST": {ADMIN_TASKS}}),
    (re.compile(r"^/admin/dlq/\{queue\}/bulk_replay$"), {"POST": {ADMIN_TASKS}}),
    (re.compile(r"^/admin/events/system/dlq/replay$"), {"POST": {ADMIN_TASKS}}),
    # Admin templates mgmt
    (re.compile(r"^/admin/templates$"), {
        "GET": {ADMIN_TASKS},
        "POST": {ADMIN_TASKS},
    }),
    (re.compile(r"^/admin/templates/roi$"), {"GET": {ADMIN_TASKS}}),
    (re.compile(r"^/admin/templates/\{template_id\}$"), {"DELETE": {ADMIN_TASKS}}),

    # Tasks (CRUD) legacy (non-/api) paths
    (re.compile(r"^/tasks$"), {
        "GET": {READ_TASKS},
        "POST": {WRITE_TASKS},
    }),
    (re.compile(r"^/tasks/\{task_id\}$"), {
        "GET": {READ_TASKS},
        "PUT": {WRITE_TASKS},
        "PATCH": {WRITE_TASKS},
        "DELETE": {WRITE_TASKS},
    }),

    # Users/admin: protect explicit admin endpoints; login remains outside RBAC map
    (re.compile(r"^/users/me$"), {
        "GET": {ADMIN_USERS},
    }),
    # API users endpoints are public in tests for registration/login
    (re.compile(r"^/api/users/register$"), {"POST": set()}),
    (re.compile(r"^/api/users/login$"), {"POST": set()}),

    # AI analysis/prediction endpoints (additive; stubbed handlers)
    (re.compile(r"^/ai/historical/ingest_and_analyze$"), {
        "POST": {READ_LEADS},
    }),
    (re.compile(r"^/ai/behavior/analyze$"), {
        "POST": {WRITE_AI},
    }),
    (re.compile(r"^/ai/predict/automate$"), {
        "POST": {WRITE_AI},
    }),

    # Self-heal endpoints (admin-only)
    (re.compile(r"^/selfheal/health$"), {
        "GET": {ADMIN_TASKS},
    }),
    (re.compile(r"^/selfheal/heal$"), {
        "POST": {ADMIN_TASKS},
    }),
    (re.compile(r"^/selfheal/rebuild$"), {
        "POST": {ADMIN_TASKS},
    }),

    # Tasks (CRUD) under /api for RBAC coverage
    (re.compile(r"^/api/tasks/?$"), {
        "GET": {READ_TASKS},
        "POST": {WRITE_TASKS},
    }),
    (re.compile(r"^/api/tasks/\{task_id\}$"), {
        "GET": {READ_TASKS},
        "PUT": {WRITE_TASKS},
        "PATCH": {WRITE_TASKS},
        "DELETE": {WRITE_TASKS},
    }),

    # Leads (CRUD) under /api for RBAC coverage
    (re.compile(r"^/api/leads/?$"), {
        "GET": {READ_LEADS},
        "POST": {READ_LEADS},
    }),
    (re.compile(r"^/api/leads/\{lead_id\}$"), {
        "GET": {READ_LEADS},
        "PUT": {READ_LEADS},
        "DELETE": {READ_LEADS},
    }),

    # Communication auto-reply under /api and legacy comm path
    (re.compile(r"^/api/auto-reply/suggest$"), {"POST": {READ_LEADS}}),
    (re.compile(r"^/api/comm/auto_reply$"), {"POST": {READ_LEADS}}),
    # Automation runs (recent list)
    (re.compile(r"^/automation/recent$"), {"GET": {READ_RUNS}}),
]

SAFE_METHODS: set[str] = {"GET", "HEAD", "OPTIONS"}


