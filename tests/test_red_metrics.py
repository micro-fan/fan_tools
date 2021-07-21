import time

import pytest

from fan_tools.red_metrics import (
    ExporterMetricItem,
    Metrics,
    MetricsStorage,
    PrometheusExporter,
    RedisMetricsStorage,
    red_metrics,
)


@pytest.fixture
def redis_url():
    return 'redis://localhost:40002/1'


@pytest.fixture
def redis_storage(redis_url):
    return RedisMetricsStorage(redis_url=redis_url)


@pytest.fixture
def metrics_data(redis_storage):
    def _create(key: str):
        redis_storage.set(f'{key}:{Metrics.duration.value}', 0.5)
        redis_storage.incr(f'{key}:{Metrics.requests_count.value}')
        redis_storage.incr(f'{key}:{Metrics.errors_count.value}')
        for i in range(50):
            redis_storage.sliding_window(f'{key}:{Metrics.duration_value.value}', i)

    yield _create


class TestREDMetricsDecorator:
    def test_success(self, redis_storage):
        metric = red_metrics(name='test_metric', storage=redis_storage)
        assert metric(lambda: 'baz')() == 'baz'

    def test_without_storage(self):
        metric = red_metrics(name='test_metric')
        assert metric(lambda: 'baz')() == 'baz'

    def test_not_implemented_storage(self):
        metric = red_metrics(name='test_metric', storage=MetricsStorage())
        with pytest.raises(NotImplementedError):
            metric(lambda: 'baz')()


class TestRedisMetricsStorage:
    def test_invalid_redis_url(self):
        with pytest.raises(ValueError) as exc:
            RedisMetricsStorage(redis_url='invalid_redis_url')
        assert (
            str(exc.value)
            == 'Redis URL must specify one of the following schemes (redis://, rediss://, unix://)'
        )

    def test_incr(self, redis_storage):
        key = 'incr_key'
        redis_storage.incr(key)
        assert int(redis_storage.get(key)) == 1

    def test_set(self, redis_storage):
        key = 'set_key'
        redis_storage.set(key, 123)
        assert int(redis_storage.get(key)) == 123

    def test_sliding_window(self, redis_storage):
        key = 'sliding_window_key'
        for i in range(5):
            redis_storage.sliding_window(key, i)
        keys = redis_storage.connection.scan(cursor=0, match=f'{key}:*')[1]
        metrics = redis_storage._fetch_metrics(keys)
        metrics = [int(metric) for metric in metrics.values()]
        assert set(metrics) == set(list(range(5)))

    def test_get_metrics(self, redis_storage, metrics_data):
        key = 'metric'
        metrics = redis_storage.get_metrics(key)
        assert metrics == [
            f'{key}_requests_count 0',
            f'{key}_errors_count 0',
            f'{key}_duration 0',
            f'{key}_duration_avg 0',
        ]

        metrics_data(key)
        metrics = redis_storage.get_metrics(key)
        assert metrics == [
            f'{key}_requests_count 1',
            f'{key}_errors_count 1',
            f'{key}_duration 0.5',
            f'{key}_duration_avg 44.5',
        ]
        metrics = redis_storage.get_metrics(key, mean_count=3)
        assert metrics == [
            f'{key}_requests_count 1',
            f'{key}_errors_count 1',
            f'{key}_duration 0.5',
            f'{key}_duration_avg 48.0',
        ]


class TestPrometheusExporter:
    def test_without_storage(self):
        exporter = PrometheusExporter()
        assert exporter.metrics() == []

    def test_metrics(self, redis_storage, metrics_data):
        metrics_data('simple_metric')
        exporter = PrometheusExporter(storage=redis_storage)
        assert exporter.metrics(
            metrics=[
                ExporterMetricItem(name='simple_metric'),
                ExporterMetricItem(name='not_exists_metric'),
            ]
        ) == [
            'simple_metric_requests_count 1',
            'simple_metric_errors_count 1',
            'simple_metric_duration 0.5',
            'simple_metric_duration_avg 44.5',
            'not_exists_metric_requests_count 0',
            'not_exists_metric_errors_count 0',
            'not_exists_metric_duration 0',
            'not_exists_metric_duration_avg 0',
        ]


def test_decorator_and_exporter(redis_storage):
    metric = red_metrics(name='test', storage=redis_storage)
    for _ in range(3):
        metric(lambda: time.sleep(0.1))()
    try:
        metric(lambda: 1 / 0)()
    except ZeroDivisionError:
        pass
    exporter = PrometheusExporter(storage=redis_storage)
    metrics = exporter.metrics(
        metrics=[
            ExporterMetricItem(name='test'),
        ]
    )
    assert len(metrics) == 4
    assert 'test_requests_count 3' in metrics
    assert 'test_errors_count 1' in metrics
