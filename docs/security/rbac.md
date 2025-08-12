# RBAC (Route → Scope) Guidance

This project uses a scope-based RBAC model. Scopes are strings like `runs:read` or `runs:write`.

## Scopes

Defined in `backend/app/security/scopes.py`:
- `runs:read`
- `runs:write`
- `tasks:admin`
- `users:admin`

## Route → Scope Map

Canonical map lives in `backend/app/security/rbac_map.py`. It associates regex path patterns with required scopes by HTTP method. Example:

```python
(re.compile(r^/api/runs$), {
    "GET":  {READ_RUNS},
    "POST": {WRITE_RUNS},
})
```

## Attaching Enforcement

Use `require_scopes` dependency from `backend/app/security/deps.py` on routers. Example:

```python
@router.get("", dependencies=[Depends(require_scopes({READ_RUNS}))])
```

## Tests / Enforcement

- `backend/tests/security/test_rbac_route_coverage.py` fails if:
  - an unsafe method is missing `require_scopes`
  - a route is missing from the RBAC map
  - an entry has an empty scope set
- `backend/tests/security/test_rbac_matrix.py` fails on conflicting regex entries for the same method.

## Adding New Routes

1. Update `rbac_map.py` with a proper regex and scopes.
2. Attach `require_scopes` to the router endpoint.
3. Run `pytest` to confirm RBAC coverage.
