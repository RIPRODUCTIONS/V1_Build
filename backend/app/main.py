import os
from urllib.parse import urlparse

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.db import engine as sa_engine
from app.routers.admin import router as admin_router
from app.routers.agent import router as agent_router
from app.routers.auth import router as auth_router
from app.routers.auto_reply import router as auto_reply_router
from app.routers.health import router as health_router
from app.routers.leads import router as leads_router
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router

# Optional OpenTelemetry imports
try:  # pragma: no cover - optional dependency
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    HAS_OTEL = True
except Exception:  # pragma: no cover - optional dependency not installed
    HAS_OTEL = False


def create_app() -> FastAPI:
    # Sentry (optional)
    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.05)
    # OpenTelemetry (optional)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if HAS_OTEL and otlp_endpoint:
        resource = Resource.create({"service.name": "builder-api"})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces"))
        )
        trace.set_tracer_provider(provider)

    app = FastAPI(title="Builder API", version="0.1.0", redirect_slashes=False)
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS") or os.getenv("NEXT_PUBLIC_WEB_ORIGIN")
    if allowed_origins_env:
        candidates = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    else:
        candidates = ["http://localhost:3000"]

    def _valid_origin(o: str) -> bool:
        try:
            p = urlparse(o)
            return p.scheme in ("http", "https") and bool(p.netloc)
        except Exception:
            return False

    allowed_origins = [o for o in candidates if _valid_origin(o)]
    if not allowed_origins:
        allowed_origins = ["http://localhost:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Instrument after app is created
    if HAS_OTEL:
        try:
            FastAPIInstrumentor.instrument_app(app)
            RequestsInstrumentor().instrument()
            SQLAlchemyInstrumentor().instrument(engine=sa_engine.sync_engine)
        except Exception:
            # If instrumentation fails at runtime, continue without tracing
            pass

    app.include_router(health_router)
    app.include_router(auto_reply_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(leads_router)
    app.include_router(tasks_router)
    app.include_router(agent_router)
    app.include_router(admin_router)
    Base.metadata.create_all(bind=engine)
    return app


app = create_app()
