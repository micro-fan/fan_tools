import asyncio
import datetime
import functools
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from statistics import mean
from typing import List, Optional, Union

import redis

logger = logging.getLogger(__name__)


def extend_enum(inherited_enum):
    def wrapper(added_enum):
        joined = {}
        for item in inherited_enum:
            joined[item.name] = item.value
        for item in added_enum:
            joined[item.name] = item.value
        return Enum(added_enum.__name__, joined)

    return wrapper


class SimpleMetrics(Enum):
    requests_count = 'requests_count'
    errors_count = 'errors_count'
    duration = 'duration'

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


@extend_enum(SimpleMetrics)
class Metrics(Enum):
    duration_value = 'duration_value'


class MetricsStorage:
    simple_metrics = SimpleMetrics.list()

    def incr(self, key):
        raise NotImplementedError

    def set(self, key: str, value: Union[int, float]):
        raise NotImplementedError

    def get(self, key: str):
        raise NotImplementedError

    def sliding_window(self, key: str, value: Union[int, float]):
        raise NotImplementedError

    def get_metrics(self, key: str, mean_count: int = 10) -> List[str]:
        raise NotImplementedError


class RedisMetricsStorage(MetricsStorage):
    def __init__(self, redis_url: str = None, expiration: int = None):
        self.redis_url = redis_url
        self.connection = self.connect()
        self.expiration = expiration or 60 * 60 * 24 * 30

    def connect(self) -> Optional[redis.Redis]:
        if not self.redis_url:
            return None
        try:
            r = redis.Redis().from_url(self.redis_url)
            r.ping()
            return r
        except redis.connection.ConnectionError:
            return None

    def get(self, key: str):
        return self.connection.get(key)

    def incr(self, key: str):
        self.connection.incr(key)

    def sliding_window(self, key: str, value: Union[int, float]):
        ts = int(datetime.datetime.now().timestamp() * 1_000_000)
        key = f'{key}:{ts}'
        self.connection.set(key, value, ex=self.expiration)

    def set(self, key: str, value: Union[int, float]):
        self.connection.set(key, value, ex=self.expiration)

    def _get_metric_keys(self, key: str, mean_count: int = 10):
        keys = self.connection.scan_iter(
            match=f'{key}:{Metrics.duration_value.value}:*',
            count=1000,
        )
        to_delete = []
        metrics_keys = [f'{key}:{metric}' for metric in self.simple_metrics]
        metric_duration_keys = []
        for i in keys:
            if f'{key}:{Metrics.duration_value.value}:'.encode() in i:
                metric_duration_keys.append(i.decode())
        metric_duration_keys.sort()
        metrics_keys.extend(metric_duration_keys[-mean_count:])
        to_delete.extend(metric_duration_keys[:-mean_count])
        return metrics_keys, to_delete

    def _fetch_metrics(self, metric_keys: List[str]):
        metrics = self.connection.mget(metric_keys)
        items = dict(zip(metric_keys, metrics))
        return items

    def _get_metrics(self, key: str, metrics: dict) -> List[str]:
        result = []
        for metric in self.simple_metrics:
            _key = f'{key}:{metric}'
            val = metrics.pop(_key)
            result.append(f'{key}_{metric} {val.decode() if val else 0}')
        duration_key = f'{key}:{Metrics.duration_value.value}:'
        values = [float(v) for i, v in metrics.items() if str(i).startswith(duration_key)]
        value = mean(values) if values else 0
        result.append(f'{key}_duration_avg {value}')
        return result

    def get_metrics(self, key: str, mean_count: int = 10) -> List[str]:
        metric_keys, expired_keys = self._get_metric_keys(key, mean_count=mean_count)
        if expired_keys:
            self.connection.delete(*expired_keys)
        metrics = self._fetch_metrics(metric_keys)
        return self._get_metrics(key=key, metrics=metrics)


def red_metrics(name: str = None, storage: MetricsStorage = None):
    """
    Decorator for serve RED (Read, Error, Duration) metrics.
    Usage:
    >>> redis_storage = RedisMetricsStorage('redis://localhost:6379/1')
    ... @red_metrics(name='some_code_metrics', storage=redis_storage):
    ... def some_code_to_profile()
    """

    def get_metric_name(func, name: str = None) -> str:
        return name or f'{func.__module__}.{func.__name__}'

    @contextmanager
    def prometheus_context(name: str):
        start = time.time()
        is_success = True
        try:
            yield
        except:  # noqa 722
            is_success = False
            raise
        finally:
            if not storage:
                return
            execution_time = time.time() - start
            if is_success:
                storage.incr(f'{name}:{Metrics.requests_count.value}')
            else:
                storage.incr(f'{name}:{Metrics.errors_count.value}')
            storage.sliding_window(f'{name}:{Metrics.duration_value.value}', execution_time)
            storage.set(f'{name}:duration', execution_time)

    def wrapper(func):
        metric_name = get_metric_name(func, name)
        if not asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                with prometheus_context(name=metric_name):
                    return func(*args, **kwargs)

        else:

            @functools.wraps(func)
            async def wrapped(*args, **kwargs):
                with prometheus_context(name=metric_name):
                    return await func(*args, **kwargs)

        return wrapped

    return wrapper


@dataclass
class ExporterMetricItem:
    name: str
    mean_count: int = 10


class PrometheusExporter:
    """
    Decorator for providing RED (Read, Error, Duration) metrics.
    Usage:
    >>> redis_storage = RedisMetricsStorage('redis://localhost:6379/1')
    ... exporter = PrometheusExporter(storage=redis_storage)
    ... exporter.metrics([ExporterMetricItem(name='some_code_metrics', mean_count=5)])
    """

    def __init__(self, storage: MetricsStorage = None):
        self.storage = storage

    def metrics(self, metrics: List[ExporterMetricItem] = None) -> List[str]:
        if not self.storage or not metrics:
            return []
        result = []
        for metric in metrics:
            metric_result = self.storage.get_metrics(
                key=metric.name,
                mean_count=metric.mean_count,
            )
            result.extend(metric_result)
        return result
