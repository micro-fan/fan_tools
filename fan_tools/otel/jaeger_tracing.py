from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from fan_tools.otel import instrument_django, instrument_logging, instrument_psycopg2


def setup_jaeger_tracer(env, service, host, port, additional={}):
    resource = Resource(
        attributes={'service.name': service, 'env': env, 'dd.service': service, **additional}
    )
    trace.set_tracer_provider(TracerProvider(resource=resource))
    trace.get_tracer_provider().get_tracer(__name__)

    jaeger_exporter = JaegerExporter(
        agent_host_name=host,
        agent_port=port,
    )

    trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(jaeger_exporter))


INS_DJANGO = [instrument_django, instrument_logging, instrument_psycopg2]


def enable_otel(env, service, host='otlp', port=6831, instrumentations=INS_DJANGO, additional={}):
    for instrument in instrumentations:
        instrument()
    setup_jaeger_tracer(env, service, host, port, additional)
