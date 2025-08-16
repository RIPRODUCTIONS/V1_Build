#!/usr/bin/env python3
"""
Extended server launcher that includes new routers safely.
This doesn't modify server.py but adds the new functionality.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure ai_framework module is importable
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from routers.auth_router import router as auth_router  # type: ignore
from routers.files_router import router as files_router  # type: ignore
from routers.integrations_router import router as integrations_router  # type: ignore
from routers.users_router import router as users_router  # type: ignore
from server import AIFrameworkServer  # type: ignore


def build_app() -> FastAPI:
    server = AIFrameworkServer()
    # Create a FastAPI app without full async startup to avoid None app
    app = server._create_fastapi_app()
    try:
        app.include_router(auth_router)
        app.include_router(users_router)
        app.include_router(files_router)
        app.include_router(integrations_router)
        print("✅ Extended routers loaded successfully")
    except Exception as e:  # pragma: no cover
        print(f"⚠️  Some routers not available: {e}")
        print("Server will run with basic functionality")
    return app


app = build_app()


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8001"))
    print(f"🚀 Starting extended AI Framework server on {host}:{port}")
    print("📊 Diagnostics available at /api/diagnostics")
    # Pass module:var path to avoid ASGI detection issues
    uvicorn.run("run_server_extended:app", host=host, port=port, reload=False)


