import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_NAMESPACE, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from uvicorn.logging import AccessFormatter, DefaultFormatter

from config import settings


class _TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        ctx = trace.get_current_span().get_span_context()
        record.trace_id = format(ctx.trace_id, "032x") if ctx.is_valid else ""
        return True


class _TraceDefaultFormatter(DefaultFormatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        trace_id = getattr(record, "trace_id", "")
        return f"{msg} [trace_id={trace_id}]" if trace_id else msg


class _TraceAccessFormatter(AccessFormatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        trace_id = getattr(record, "trace_id", "")
        return f"{msg} [trace_id={trace_id}]" if trace_id else msg


def _install_trace_logging() -> None:
    filt = _TraceContextFilter()

    uvicorn_logger = logging.getLogger("uvicorn")
    for handler in uvicorn_logger.handlers:
        handler.addFilter(filt)
        handler.setFormatter(_TraceDefaultFormatter())

    access_logger = logging.getLogger("uvicorn.access")
    for handler in access_logger.handlers:
        handler.addFilter(filt)
        handler.setFormatter(_TraceAccessFormatter())


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
    _install_trace_logging()
