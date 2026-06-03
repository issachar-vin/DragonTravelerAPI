from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_NAMESPACE, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import settings


def setup_telemetry(app: FastAPI) -> None:
    if not settings.otel_enabled:
        return

    endpoint = settings.otel_exporter_otlp_endpoint

    resource = Resource.create(
        {
            SERVICE_NAME: "DragonTravelerAPI",
            SERVICE_NAMESPACE: "dragontraveler",
        }
    )

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    PymongoInstrumentor().instrument()
    FastAPIInstrumentor().instrument_app(app)
