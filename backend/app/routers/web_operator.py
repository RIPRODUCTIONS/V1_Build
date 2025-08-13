from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from urllib.parse import urlparse
from celery.result import AsyncResult
from app.agent.celery_app import celery_app
from app.operator.mvp_web_executor import MVPWebExecutor


router = APIRouter(prefix="/operator/web", tags=["operator:web"])


@router.post("/tasks")
async def create_web_automation_task(task: Dict[str, Any], settings=Depends(get_settings)) -> Dict[str, Any]:
    if not settings.OPERATOR_WEB_ENABLED:
        return {"status": "disabled", "message": "Web operator disabled"}
    try:
        from app.tasks.web_automation_tasks import execute_web_automation_task

        async_result = execute_web_automation_task.delay({
            "description": task.get("description", ""),
            "url": task.get("url"),
            "correlation_id": task.get("correlation_id"),
        })
        return {"status": "queued", "task_id": async_result.id}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/tasks/{task_id}")
async def get_web_task_status(task_id: str, settings=Depends(get_settings)) -> Dict[str, Any]:
    if not settings.OPERATOR_WEB_ENABLED:
        return {"status": "disabled", "task_id": task_id}
    try:
        r = AsyncResult(task_id, app=celery_app)
        if r.successful():
            return {"status": "completed", "task_id": task_id, "result": r.result}
        if r.failed():
            return {"status": "failed", "task_id": task_id, "error": str(r.result)}
        return {"status": r.state.lower(), "task_id": task_id}
    except Exception as exc:
        return {"status": "error", "task_id": task_id, "detail": str(exc)}


@router.post("/demo/contact_form")
async def demo_contact_form(body: Dict[str, Any], settings=Depends(get_settings)) -> Dict[str, Any]:
    if not settings.OPERATOR_WEB_ENABLED:
        return {"status": "disabled"}
    url = body.get("url")
    form_data = body.get("form_data") or {}
    # Domain allowlist check
    try:
        allowed = settings.OPERATOR_ALLOWED_DOMAINS.split(",") if settings.OPERATOR_ALLOWED_DOMAINS else ["*"]
        host = urlparse(url or "").hostname or ""
        if allowed and allowed != ["*"] and host not in [h.strip().lower() for h in allowed]:
            return {"status": "blocked", "reason": "domain_not_allowed", "host": host}
    except Exception:
        pass
    execr = MVPWebExecutor()
    return await execr.execute_contact_form(url, form_data)


@router.get("/ui", response_class=HTMLResponse)
async def operator_ui() -> str:
    # Minimal UI to submit a demo task and view the response inline
    return """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
    <title>Operator Demo</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; }
      label { display:block; margin-top:12px; font-weight:600; }
      input, textarea { width:100%; padding:8px; margin-top:6px; box-sizing:border-box; }
      button { margin-top:16px; padding:10px 16px; font-weight:600; }
      pre { background:#0b1021; color:#e6edf3; padding:12px; overflow:auto; border-radius:6px; }
    </style>
  </head>
  <body>
    <h1>Web Operator Demo</h1>
    <p>Submit a contact form task to the operator.</p>
    <form id=\"f\">
      <label>Contact page URL
        <input type=\"url\" id=\"url\" placeholder=\"https://example.com/contact\" required />
      </label>
      <label>Name
        <input type=\"text\" id=\"name\" placeholder=\"Ada Lovelace\" />
      </label>
      <label>Email
        <input type=\"email\" id=\"email\" placeholder=\"ada@example.com\" />
      </label>
      <label>Message
        <textarea id=\"message\" rows=\"4\" placeholder=\"Hello!\"></textarea>
      </label>
      <button type=\"submit\">Run</button>
    </form>
    <h3>Result</h3>
    <pre id=\"out\"></pre>
    <script>
      const f = document.getElementById('f');
      const out = document.getElementById('out');
      f.addEventListener('submit', async (e) => {
        e.preventDefault();
        out.textContent = 'Running...';
        const payload = {
          url: document.getElementById('url').value,
          form_data: {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            message: document.getElementById('message').value,
          }
        };
        try {
          const res = await fetch('/operator/web/demo/contact_form', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          const data = await res.json();
          out.textContent = JSON.stringify(data, null, 2);
        } catch (err) {
          out.textContent = String(err);
        }
      });
    </script>
  </body>
 </html>
    """

