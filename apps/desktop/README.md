# Builder Desktop

Electron wrapper for the Builder web UI. Loads `WEB_URL` (default `http://127.0.0.1:3000`) and exposes a safe `window.builder.quickResearch(topic)` API that hits the API at `API_URL` (default `http://127.0.0.1:8000`).

Commands:

```
cd apps/desktop
npm install
npm run dev
```

Bridged APIs (renderer):
- `window.builder.runResearch(topic)` -> `{ status, task_id, result? }`
- `window.builder.getPersonalRun(taskId)` -> `{ state, status, result? }`
- `window.builder.runAgent(goal, agent)` -> `{ status, data }`


