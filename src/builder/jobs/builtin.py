from __future__ import annotations

import json
from pathlib import Path

from ..config import Settings
from . import register


@register("verify-resources")
def verify_resources() -> int:
    """Verify that core resource paths exist and are directories.

    Writes a JSON summary to stdout and returns 0 on success, 1 on failure.
    """
    settings = Settings.load()
    issues = settings.validate()

    summary = {
        "workspace_dir": str(settings.workspace_dir),
        "resource_drive": str(settings.resource_drive),
        "toolbox_20gb": str(settings.toolbox_20gb),
        "toolbox": str(settings.toolbox),
        "toolbox_backendr_2": str(settings.toolbox_backendr_2),
        "issues": issues,
    }
    print(json.dumps(summary, indent=2))
    return 0 if not issues else 1


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


@register("scaffold-backend")
def scaffold_backend() -> int:
    """Create a minimal FastAPI backend with health and auto-reply endpoints + tests."""
    root = Settings.load().workspace_dir
    backend = root / "backend"

    # Requirements
    _write_file(
        backend / "requirements.txt",
        "\n".join(
            [
                "fastapi==0.111.0",
                "uvicorn[standard]==0.30.1",
                "pydantic==2.7.1",
                "pytest==8.2.2",
                "httpx==0.27.2",
            ]
        )
        + "\n",
    )

    # App files
    _write_file(backend / "app/__init__.py", "__all__ = []\n")
    _write_file(
        backend / "app/main.py",
        (
            "from starlette.applications import Starlette\n"
            "from starlette.responses import JSONResponse\n"
            "from starlette.requests import Request\n"
            "from starlette.routing import Route\n\n"
            "async def health(_: Request):\n"
            '    return JSONResponse({"status": "ok"})\n\n'
            "def simple_auto_reply(body: str) -> str:\n"
            "    text = body.lower()\n"
            '    if any(k in text for k in ("meeting", "schedule", "call")):\n'
            '        return ("Thanks for reaching out. Happy to schedule a meeting—what times work for you this week?")\n'
            '    if any(k in text for k in ("invoice", "payment", "bill")):\n'
            '        return "Thanks for the update. I\'ll review the invoice and get back to you shortly."\n'
            '    if any(k in text for k in ("urgent", "asap", "immediately")):\n'
            '        return "Received—I\'ll look into this immediately and follow up shortly."\n'
            '    return "Thanks for your message—appreciate it. I’ll get back to you soon."\n\n'
            "async def suggest(request: Request):\n"
            "    payload = await request.json()\n"
            '    body = (payload or {}).get("body", "")\n'
            "    if not isinstance(body, str) or not body.strip():\n"
            '        return JSONResponse({"detail": "body is required"}, status_code=400)\n'
            '    return JSONResponse({"reply": simple_auto_reply(body)})\n\n'
            'routes = [\n    Route("/health", health, methods=["GET"]),\n    Route("/auto-reply/suggest", suggest, methods=["POST"]),\n]\n\n'
            "app = Starlette(routes=routes)\n"
        ),
    )

    # Tests
    _write_file(
        backend / "tests/test_health.py",
        (
            "from fastapi.testclient import TestClient\n"
            "from app.main import app\n\n"
            "client = TestClient(app)\n\n"
            "def test_health():\n"
            '    res = client.get("/health")\n'
            "    assert res.status_code == 200\n"
            '    assert res.json()["status"] == "ok"\n'
        ),
    )
    _write_file(
        backend / "tests/test_auto_reply.py",
        (
            "from fastapi.testclient import TestClient\n"
            "from app.main import app\n\n"
            "client = TestClient(app)\n\n"
            "def test_auto_reply_basic():\n"
            '    res = client.post("/auto-reply/suggest", json={"body": "Let\'s schedule a meeting"})\n'
            "    assert res.status_code == 200\n"
            '    assert "schedule" in res.json()["reply"].lower()\n\n'
            "def test_auto_reply_requires_body():\n"
            '    res = client.post("/auto-reply/suggest", json={"body": "  "})\n'
            "    assert res.status_code == 400\n"
        ),
    )

    return 0


@register("scaffold-ci")
def scaffold_ci() -> int:
    """Add a minimal GitHub Actions workflow for backend tests."""
    root = Settings.load().workspace_dir
    ci = root / ".github/workflows/ci.yml"
    _write_file(
        ci,
        (
            "name: CI\n"
            "on:\n  push:\n  pull_request:\n"
            "jobs:\n  backend-tests:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n"
            "      - name: Install deps\n        run: |\n          python -m venv .venv\n          . .venv/bin/activate\n          pip install -r backend/requirements.txt\n          pip install pytest\n"
            "      - name: Run tests\n        run: |\n          . .venv/bin/activate\n          PYTHONPATH=backend pytest -q backend/tests\n"
        ),
    )
    return 0


@register("scaffold-all")
def scaffold_all() -> int:
    """Run all scaffold jobs (backend + CI). Frontend placeholder is deferred."""
    rc1 = scaffold_backend()
    rc2 = scaffold_ci()
    return 0 if rc1 == 0 and rc2 == 0 else 1
