import asyncio
import functools

import sentry_sdk


def sentry_child_transaction(name: str):
    def sentry_context(name: str):
        span = sentry_sdk.Hub.current.scope.span
        if span is None:
            return sentry_sdk.start_transaction(name=name)
        else:
            return span.start_child(op=name)

    def wrapper(func):
        if not asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                with sentry_context(name=name):
                    return func(*args, **kwargs)

        else:

            @functools.wraps(func)
            async def wrapped(*args, **kwargs):
                with sentry_context(name=name):
                    return await func(*args, **kwargs)

        return wrapped

    return wrapper
