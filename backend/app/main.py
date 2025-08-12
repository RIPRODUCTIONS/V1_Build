import os
from urllib.parse import urlparse

import sentry_sdk
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.db import engine as sa_engine
from app.db import migrate_dev_sqlite

# ruff: noqa: I001
from app.reliability.circuit_breaker import SimpleCircuitBreaker
from app.reliability.metrics import SimpleTimingMetrics
from app.reliability.rate_limiter import SlidingWindowRateLimiter
from app.automation.router import router as automation_router
from app.ops.cursor_bridge import router as cursor_bridge
from app.ops.metrics import setup_metrics
from app.ops.internal_guard import InternalTokenGuard
from app.middleware.correlation import CorrelationMiddleware
from app.obs.metrics import MetricsMiddleware
from contextlib import suppress
from app.routers.admin import router as admin_router
from app.routers.agent import router as agent_router
from app.routers.ai_agents import router as ai_agents_router
from app.routers.auth import router as auth_router
from app.routers.auto_reply import router as auto_reply_router
from app.routers.content import router as content_router
from app.routers.health import router as health_router
from app.routers.leads import router as leads_router
from app.routers.physical import router as physical_router
from app.routers.predictive import router as predictive_router
from app.routers.ideation import router as ideation_router
from app.routers.finance import router as finance_router
from app.routers.prototype import router as prototype_router
from app.routers.relationship import router as relationship_router
from app.routers.business import router as business_router
from app.routers.documents import router as documents_router
from app.routers.life import router as life_router
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router
from app.routers.comm import router as comm_router
from app.routers.departments import router as departments_router
from app.routers.research import router as research_router
from app.routers.debug import router as debug_router
from app.observability import setup_observability
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.body_limit import BodyLimitMiddleware

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


def _wire_instrumentation(app: FastAPI) -> None:
    # Instrument after app is created
    if HAS_OTEL:
        try:
            FastAPIInstrumentor.instrument_app(app)
            RequestsInstrumentor().instrument()
            SQLAlchemyInstrumentor().instrument(engine=sa_engine.sync_engine)
        except Exception:
            pass
    # Reliability middlewares
    app.add_middleware(SimpleTimingMetrics)
    app.add_middleware(SimpleCircuitBreaker)
    app.add_middleware(SlidingWindowRateLimiter)
    with suppress(Exception):
        setup_metrics(app)


def create_app() -> FastAPI:
    # Sentry (optional)
    dsn = os.getenv('SENTRY_DSN')
    if dsn:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.05)
    # OpenTelemetry (optional)
    otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    if HAS_OTEL and otlp_endpoint:
        resource = Resource.create({'service.name': 'builder-api'})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f'{otlp_endpoint}/v1/traces'))
        )
        trace.set_tracer_provider(provider)

    app = FastAPI(title='Builder API', version='0.1.0', redirect_slashes=False)

    # Setup observability (Layer 10)
    setup_observability(app, service_name='ai-business-engine-backend')

    allowed_origins_env = os.getenv('ALLOWED_ORIGINS') or os.getenv('NEXT_PUBLIC_WEB_ORIGIN')
    if allowed_origins_env:
        candidates = [o.strip() for o in allowed_origins_env.split(',') if o.strip()]
    else:
        candidates = ['http://localhost:3000']

    def _valid_origin(o: str) -> bool:
        try:
            p = urlparse(o)
            return p.scheme in ('http', 'https') and bool(p.netloc)
        except Exception:
            return False

    allowed_origins = [o for o in candidates if _valid_origin(o)]
    if not allowed_origins:
        allowed_origins = ['http://localhost:3000']
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
        allow_headers=['Authorization', 'Content-Type', 'X-Request-ID'],
        expose_headers=['X-Request-ID'],
    )
    # Boot logging middleware (catches startup errors)
    from app.middleware.bootlog import BootLogMiddleware

    app.add_middleware(BootLogMiddleware)
    app.add_middleware(BodyLimitMiddleware, max_bytes=2_000_000)

    # Correlation and labeled metrics
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(MetricsMiddleware)
    from app.core.config import get_settings as _gs
    _st = _gs()
    app.add_middleware(SecurityHeadersMiddleware, csp_report_only=not _st.FEATURE_STRICT_CSP)

    # Error envelope middleware (prevents crashes)
    from app.middleware.error_envelope import ErrorEnvelopeMiddleware

    app.add_middleware(ErrorEnvelopeMiddleware)
    # Security toggle: protect /cursor and /ops routes when SECURE_MODE is set
    app.add_middleware(InternalTokenGuard)
    _wire_instrumentation(app)

    app.include_router(health_router)
    app.include_router(auto_reply_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(comm_router)
    app.include_router(leads_router)
    app.include_router(tasks_router)
    app.include_router(agent_router)
    app.include_router(admin_router)
    # New additive routers
    app.include_router(ai_agents_router)
    app.include_router(predictive_router)
    app.include_router(content_router)
    app.include_router(physical_router)
    app.include_router(ideation_router)
    app.include_router(finance_router)
    app.include_router(relationship_router)
    app.include_router(business_router)
    app.include_router(documents_router)
    app.include_router(life_router)
    app.include_router(departments_router)
    app.include_router(prototype_router)
    app.include_router(automation_router)
    app.include_router(cursor_bridge)
    # Back-compat: include legacy /runs router if available for tests
    try:
        from app.routers import runs as runs_router  # type: ignore

        app.include_router(runs_router.router)
    except Exception:
        pass
    app.include_router(research_router)
    app.include_router(debug_router)

    # Log registered skills and DAGs on startup
    try:
        from app.automation.registry import _SKILLS, _DAGS

        print(f'🚀 Registered skills: {list(_SKILLS.keys())}')
        print(f'🚀 Registered DAGs: {list(_DAGS.keys())}')

        # Check for specific intents we need
        required_intents = ['ideation.generate', 'research.validate_idea']
        for intent in required_intents:
            if intent in _DAGS:
                print(f"✅ DAG '{intent}' registered")
            elif intent in _SKILLS:
                print(f"✅ Skill '{intent}' registered")
            else:
                print(f"❌ Intent '{intent}' NOT found in registry")

    except Exception as e:
        print(f'⚠️ Could not log registry: {e}')
        import traceback

        traceback.print_exc()

    # Database initialization (optional for dev)
    from app.core.config import get_settings

    settings = get_settings()
    if not getattr(settings, 'SKIP_DB_INIT', False):
        try:
            Base.metadata.create_all(bind=engine)
            # Dev/CI sqlite additive migrations (ignore errors on non-sqlite)
            with suppress(Exception):  # pragma: no cover
                migrate_dev_sqlite()
        except Exception as e:
            print(f'⚠️ Database initialization failed (continuing): {e}')

    return app


app = create_app()


def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version='0.1.0',
        routes=app.routes,
    )
    components = schema.setdefault('components', {}).setdefault('securitySchemes', {})
    components.setdefault(
        'bearerAuth',
        {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        },
    )
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _custom_openapi
