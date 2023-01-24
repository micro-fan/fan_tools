# pyright: strict
import asyncio
import functools
import logging
from typing import Awaitable, Callable, ParamSpec, Type, TypeVar, Union


default_logger = logging.getLogger('fantools.python')
R = TypeVar('R')
P = ParamSpec('P')


def retry(
    exceptions: Type[Exception] = Exception,
    tries: int = -1,
    logger: logging.Logger = default_logger,
):
    """
    Executes a function and retries it if it failed.

    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param logger: will record a call retry warning.
    """

    def decorator(func: Callable[P, R]) -> Union[Callable[P, R], Callable[P, Awaitable[R]]]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                nonlocal tries
                f = functools.partial(func, *args, **kwargs)
                while tries:
                    try:
                        return await f()
                    except exceptions as e:
                        tries -= 1
                        if not tries:
                            raise
                        logger.exception('%s, retrying...', e)
                raise ValueError('tries must be greater than 0')

            return async_wrapper
        else:

            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                nonlocal tries
                f = functools.partial(func, *args, **kwargs)
                while tries:
                    try:
                        return f()
                    except exceptions as e:
                        tries -= 1
                        if not tries:
                            raise
                        logger.exception('%s, retrying...', e)
                raise ValueError('tries must be greater than 0')

        return wrapper

    return decorator
