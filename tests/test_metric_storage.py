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

    def test_03_reset(self):
        storage = MetricStorage()
        assert storage.get_metrics() == {'test_key': 2, 'test_key_new': 1}

        storage.reset()
        assert storage.get_metrics() == {}
