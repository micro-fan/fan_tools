import pytest

from fan_tools.container_utils import MetricStorage


class TestMetricStorage:
    def test_01_init(self):
        storage = MetricStorage()
        assert storage.get_metrics() == {}

    def test_02_increment(self):
        storage = MetricStorage()
        storage.increment('test_key')
        storage.increment('test_key')
        assert storage.get_metrics() == {'test_key': 2}

        storage = MetricStorage()
        storage.increment('test_key_new')
        assert storage.get_metrics() == {'test_key': 2, 'test_key_new': 1}

    def test_03_push(self):
        storage = MetricStorage()
        storage.push('push_metric', 123)
        storage.push('push_metric', 321)
        assert storage.get_metrics() == {
            'test_key': 2,
            'test_key_new': 1,
            'push_metric': [123, 321],
        }

    def test_04_reset(self):
        storage = MetricStorage()
        assert storage.get_metrics() == {
            'test_key': 2,
            'test_key_new': 1,
            'push_metric': [123, 321],
        }

        storage.reset()
        assert storage.get_metrics() == {}

    def test_05_incorrect_types(self):
        storage = MetricStorage()
        storage.push('metric', 123)
        with pytest.raises(ValueError) as exc:
            storage.increment('metric')
        assert str(exc.value) == 'Metric not support incrementing'

        storage.reset()
        assert storage.get_metrics() == {}

        storage.increment('metric')
        with pytest.raises(ValueError) as exc:
            storage.push('metric', 123)
        assert str(exc.value) == 'Metric not support pushing'
