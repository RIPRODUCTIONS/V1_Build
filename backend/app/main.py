import os
from urllib.parse import urlparse

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.db import engine as sa_engine

# ruff: noqa: I001
from app.reliability.circuit_breaker import SimpleCircuitBreaker
from app.reliability.metrics import SimpleTimingMetrics
from app.reliability.rate_limiter import SlidingWindowRateLimiter
from app.automation.router import router as automation_router
from app.ops.cursor_bridge import router as cursor_bridge
from app.ops.metrics import setup_metrics
from app.ops.internal_guard import InternalTokenGuard
from app.ops.secure_headers import SecureHeadersMiddleware
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
from app.life.router import router as life_orch_router
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router
from app.routers.comm import router as comm_router
from app.routers.runs import router as runs_router
from app.ai.router import router as ai_router
from app.selfheal.router import router as selfheal_router
from app.selfheal.services import SelfHealingCore
from app.integrations.router import router as integrations_router
from app.integrations.webhooks import router as webhook_router
from app.automations.router import router as automations_router
from app.routers.assistant import router as assistant_router
from app.routers.web_operator import router as web_operator_router
from app.routers.desktop_operator import router as desktop_operator_router
from app.routers.ai_decision import router as ai_decision_router
from app.routers.operator_gateway import router as operator_gateway_router
from app.routers.operator_runs import router as operator_runs_router
from app.routers.template_library import router as template_library_router
from app.routers.runs import router as automation_runs_router, automation_router as recent_runs_router
from app.routers.operator_metrics import router as operator_metrics_router
from app.routers.marketplace import router as marketplace_router
from app.routers.onboarding import router as onboarding_router
from app.core.config import get_settings
from app.automations.tasks import consume_event_stream
from app.operator.template_seed import seed_templates

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
    # Start system event consumer if enabled (independent of OTEL availability)
    try:
        settings = get_settings()
        if settings.SYSTEM_EVENT_CONSUMER_ENABLED:
            from app.agent.pipeline import start_event_consumer

            app.state.event_consumer_task = __import__("asyncio").create_task(start_event_consumer())
    except Exception:
        pass
    # Reliability middlewares
    app.add_middleware(SimpleTimingMetrics)
    app.add_middleware(SimpleCircuitBreaker)
    app.add_middleware(SlidingWindowRateLimiter)
    with suppress(Exception):
        setup_metrics(app)


def _required_secrets() -> list[str]:
    # Minimal set to boot in production; extend as needed
    return [
        "JWT_SECRET",
    ]


def _fail_fast_if_missing_secrets() -> None:
    env = os.getenv("ENV", "").lower()
    if env in {"production", "prod"}:
        missing: list[str] = []
        for key in _required_secrets():
            if not os.getenv(key):
                missing.append(key)
        if missing:
            # Clear, actionable error for CI/runtime
            raise RuntimeError(
                f"Missing required secrets for production: {', '.join(missing)}. "
                "Configure via environment (no .env files in production)."
            )


def create_app() -> FastAPI:
    # Best-effort: load secrets from AWS if configured (prod only)
    try:
        from app.core.secrets_aws import maybe_load_from_aws  # type: ignore

        maybe_load_from_aws()
    except Exception:
        pass
    _fail_fast_if_missing_secrets()
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
    # Security toggle: protect /cursor and /ops routes when SECURE_MODE is set
    app.add_middleware(InternalTokenGuard)
    app.add_middleware(SecureHeadersMiddleware)
    _wire_instrumentation(app)

    # Mount health under /api for consistent probes and also legacy root paths
    app.include_router(health_router, prefix="/api")
    app.include_router(health_router)
    app.include_router(auto_reply_router, prefix="/api")
    app.include_router(auto_reply_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(comm_router, prefix="/api")
    app.include_router(comm_router)
    app.include_router(leads_router, prefix="/api")
    app.include_router(leads_router)
    app.include_router(tasks_router, prefix="/api")
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
    app.include_router(life_orch_router)
    app.include_router(runs_router)
    app.include_router(ai_router)
    app.include_router(selfheal_router)
    app.include_router(integrations_router)
    app.include_router(webhook_router)
    app.include_router(automations_router)
    app.include_router(assistant_router)
    app.include_router(web_operator_router)
    app.include_router(desktop_operator_router)
    app.include_router(ai_decision_router)
    app.include_router(operator_gateway_router)
    app.include_router(operator_runs_router)
    app.include_router(template_library_router)
    app.include_router(automation_runs_router)
    app.include_router(recent_runs_router)
    app.include_router(operator_metrics_router)
    app.include_router(marketplace_router)
    app.include_router(onboarding_router)
    app.include_router(prototype_router)
    app.include_router(automation_router)
    app.include_router(cursor_bridge)
    Base.metadata.create_all(bind=engine)
    # Seed initial templates (idempotent)
    try:
        from app.db import SessionLocal

        db = SessionLocal()
        try:
            seed_templates(db)
        finally:
            db.close()
    except Exception:
        pass

    # Legacy healthz route for back-compat with tests and external probes
    @app.get("/healthz")
    async def _healthz():  # pragma: no cover - trivial
        return {"status": "ok"}

    # Background self-heal loop
    heal_core = SelfHealingCore()
    stop_event = __import__("asyncio").Event()

    @app.on_event("startup")
    async def _start_background_tasks() -> None:  # pragma: no cover - lifecycle wiring
        app.state.selfheal_stop_event = stop_event
        app.state.selfheal_task = __import__("asyncio").create_task(
            heal_core.continuous_health_monitoring(stop_event)
        )
        # Start automation consumer if enabled
        try:
            settings = get_settings()
            if settings.AUTOMATION_ENGINE_ENABLED:
                consume_event_stream.delay()
        except Exception:
            pass

    @app.on_event("shutdown")
    async def _stop_background_tasks() -> None:  # pragma: no cover - lifecycle wiring
        try:
            stop_event.set()
            t = getattr(app.state, "selfheal_task", None)
            if t is not None:
                await t
        except Exception:
            pass
    return app


app = create_app()
