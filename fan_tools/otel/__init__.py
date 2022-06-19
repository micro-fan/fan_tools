import logging

from opentelemetry.trace import (
    get_current_span,
    get_tracer,
    get_tracer_provider,
    INVALID_SPAN,
    INVALID_SPAN_CONTEXT,
)

from fan_tools.fan_logging import JSFormatter


class OtelJSFormatter(JSFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required_fields.extend(['otelSpanID', 'otelTraceID', 'otelServiceName'])


def instrument_logging(**kwargs):
    old_factory = logging.getLogRecordFactory()
    service_name = ""
    provider = kwargs.get("tracer_provider", None) or get_tracer_provider()
    resource = provider.resource if provider and hasattr(provider, 'resource') else None
    if resource:
        service_name = resource.attributes.get("service.name")

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.otelSpanID = "0"
        record.otelTraceID = "0"
        record.otelServiceName = service_name

        span = get_current_span()
        if span != INVALID_SPAN:
            ctx = span.get_span_context()
            if ctx != INVALID_SPAN_CONTEXT:
                record.otelSpanID = format(ctx.span_id, "016x")
                record.otelTraceID = format(ctx.trace_id, "032x")

                # datadog requires conversion
                record.__dict__['dd.span_id'] = str(ctx.span_id)
                record.__dict__['dd.trace_id'] = str(ctx.trace_id & 0xFFFFFFFFFFFFFFFF)

                # newrelic requires custom names
                record.__dict__['span.id'] = record.otelSpanID
                record.__dict__['trace.id'] = record.otelTraceID
        return record

    logging.setLogRecordFactory(record_factory)


def instrument_psycopg2():
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

    Psycopg2Instrumentor().instrument()
