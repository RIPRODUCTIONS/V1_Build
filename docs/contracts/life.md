### Life Service Contract

Auth: bearerAuth (JWT HS256). All POST routes require `Authorization: Bearer <token>`.

Request schema: SimpleReq
```
{
  "payload": {"type": "object", "nullable": true},
  "idempotency_key": {"type": "string", "nullable": true}
}
```

Response schema: EnqueuedResponse
```
{ "run_id": "string", "status": "queued|succeeded|failed" }
```

Routes (POST):
- /life/health/wellness
- /life/nutrition/plan
- /life/home/evening
- /life/transport/commute
- /life/learning/upskill
- /life/finance/investments
- /life/finance/bills
- /life/security/sweep
- /life/travel/plan
- /life/calendar/organize
- /life/shopping/optimize

Errors:
- 401: not_authenticated | invalid_token | token_expired | token_not_active
- 403: invalid_token (no subject)
