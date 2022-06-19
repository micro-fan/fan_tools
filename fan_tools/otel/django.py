from functools import cached_property

from django.conf import settings
from opentelemetry.instrumentation.django.middleware import _DjangoMiddleware
from opentelemetry.trace import get_tracer, get_tracer_provider

from fan_tools.otel import instrument_logging, instrument_psycopg2
from fan_tools.otel.jaeger_tracing import setup_jaeger_tracer


class OtelDjangoMiddleware(_DjangoMiddleware):
    @cached_property
    def _tracer(self):
        tracer_provider = get_tracer_provider()
        tracer = get_tracer(
            'django',
            '0.1',
            tracer_provider=tracer_provider,
        )
        return tracer


def instrument_django():
    settings.MIDDLEWARE.insert(0, 'fan_tools.otel.OtelDjangoMiddleware')


INS_DJANGO = [instrument_django, instrument_logging, instrument_psycopg2]


def enable_otel(env, service, host='otlp', port=6831, instrumentations=INS_DJANGO, additional={}):
    for instrument in instrumentations:
        instrument()
    setup_jaeger_tracer(env, service, host, port, additional)
