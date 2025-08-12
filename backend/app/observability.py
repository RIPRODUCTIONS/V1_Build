import os

import sentry_sdk
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from sentry_sdk.integrations.fastapi import FastApiIntegration

SENTRY_DSN = os.getenv('SENTRY_DSN', '')
OTLP_ENDPOINT = os.getenv('OTLP_ENDPOINT', '')  # e.g. https://otlp.yourcollector:4318/v1/traces


def setup_observability(app, service_name: str = 'backend-api'):
    # Sentry
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            environment=os.getenv('ENV', 'dev'),
            release=os.getenv('GIT_SHA', 'local'),
        )

    # OpenTelemetry Traces
    resource = Resource(attributes={SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT) if OTLP_ENDPOINT else ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    from opentelemetry import trace

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
