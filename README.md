# Builder System Runbook (Concise)

## Start stack

```
make up
```

- API: http://127.0.0.1:8000/healthz
- Web: http://127.0.0.1:3000/dashboard

## Agents

```
make agents-registry
make agents-run
```

Update agent provider/model in Web dashboard (Agents section) or POST `/ai/agents/{name}/config`.

## Coverage expansion

```
make expand-coverage
```

Enable hourly via env: `COVERAGE_EXPAND_ENABLED=true`.

## Health and self-heal

```
make health-check
```

- Security headers enforced (CSP, XFO, XCTO, Referrer, Permissions)
- Self-heal loop runs automatically; read-only status at `/health/selfheal_status`
- Alerts (optional): set `ALERT_WEBHOOK_URL`, `SLACK_WEBHOOK_URL`, or `EMAIL_*` env vars

## Desktop

```
cd apps/desktop && npm install && WEB_URL=http://127.0.0.1:3000 API_URL=http://127.0.0.1:8000 npm run dev
```

Renderer APIs: `window.builder.runResearch(topic)`, `getPersonalRun(id)`, `runAgent(goal, agent)`.

## iPhone (Expo)

```
cd apps/mobile && npm install
API_URL=http://YOUR-MAC-IP:8000 npx expo start
```

Open Expo Go, ensure phone can reach your Mac IP.

## Security Gates & Branch Protection

- Required status checks: backend (mypy), web, precommit, security
- Require PR reviews; dismiss stale approvals on new commits
- CODEOWNERS enforce review on critical paths: `backend/app/**`, `apps/web/**`, `apps/desktop/**`, `apps/mobile/**`, `.github/workflows/**`, `docker-compose.yml`
