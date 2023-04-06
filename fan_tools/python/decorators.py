# pyright: strict
import asyncio
import functools
import logging
from pathlib import Path
from typing import Awaitable, Callable, Generic, Protocol, Type, TypeVar, Union


try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec


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


class PydanticBaseModel(Protocol):
    def parse_file(self, fname: Union[str, Path]) -> 'PydanticBaseModel':
        ...

    def json(self) -> str:
        ...


ModelType = TypeVar('ModelType', bound=PydanticBaseModel)


class cache_async(Generic[ModelType]):
    """
    file cache for async functions that returns pydantic models
    NB: it doesn't use parameters to generate the cache file name
    """

    def __init__(self, fname: Path, model: ModelType, default: ModelType):
        self.fname = fname
        self._default = default
        self.cache = default
        # load from file
        if self.fname.exists():
            self.cache = model.parse_file(self.fname)

    def __call__(self, func: Callable[P, Awaitable[ModelType]]):
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> ModelType:
            if self.cache:
                return self.cache
            value = await func(*args, **kwargs)
            self.cache = value
            self.fname.write_text(self.cache.json())
            return value

        wrapper.reset_cache = self.reset_cache  # type: ignore

        return wrapper

    def reset_cache(self):
        self.cache = self._default
        if self.fname.exists():
            self.fname.unlink()
