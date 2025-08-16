import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)


class _NoopExporter(SpanExporter):
    def export(self, spans):  # type: ignore[override]
        return SpanExportResult.SUCCESS
    def shutdown(self):  # type: ignore[override]
        return None


def init_tracing(service_name: str):
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    else:
        # Attach a no-op exporter to keep SDK pathways satisfied without network calls
        provider.add_span_processor(SimpleSpanProcessor(_NoopExporter()))
    trace.set_tracer_provider(provider)
