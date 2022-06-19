from functools import cached_property

from django.conf import settings
from opentelemetry.instrumentation.django.middleware import _DjangoMiddleware
from opentelemetry.trace import get_tracer, get_tracer_provider


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
