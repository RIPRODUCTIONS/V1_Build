#!/usr/bin/env python3
"""Production Server Launcher with Enhanced Security."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

sys.path.insert(0, str(Path(__file__).parent))

from routers.auth_router import router as auth_router  # type: ignore
from routers.files_router import router as files_router  # type: ignore
from routers.integrations_router import router as integrations_router  # type: ignore
from routers.users_router import router as users_router  # type: ignore
from security_config import SecurityConfig
from server import AIFrameworkServer  # type: ignore


def build_app():
    server = AIFrameworkServer()
    app = server._create_fastapi_app()
    # routers
    try:
        app.include_router(auth_router)
        app.include_router(users_router)
        app.include_router(files_router)
        app.include_router(integrations_router)
        print("✅ Production routers loaded successfully")
    except Exception as e:
        print(f"⚠️  Some routers not available: {e}")

    # security middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=SecurityConfig.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"]
    )
    return app


app = build_app()


if __name__ == "__main__":
    keys_file = SecurityConfig.save_keys_to_file()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    workers = int(os.getenv("WORKERS", "4"))
    print("🚀 Starting PRODUCTION AI Framework server")
    print(f"📍 Host: {host}:{port}")
    print(f"👥 Workers: {workers}")
    print(f"🔐 Security keys: {keys_file}")
    uvicorn.run("run_server_production:app", host=host, port=port, workers=workers, reload=False)


