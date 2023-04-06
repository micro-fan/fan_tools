from unittest.mock import MagicMock

from fan_tools.python import cache_async


class TestCache:
    async def test_01_simplest(self, tmp_path):
        fname = tmp_path / 'cache.json'
        model = MagicMock()

        model.json.return_value = '{"a": "b"}'

        @cache_async[type(dict)](fname, model, {})
        async def func():
            return model

        assert not fname.exists()
        await func()
        assert fname.exists()
        assert fname.read_text() == '{"a": "b"}'

        func.reset_cache()
        assert not fname.exists()

    def test_02_unlink(self, tmp_path):
        fname = tmp_path / 'cache.json'
        model = MagicMock()

        model.json.return_value = '{"a": "b"}'

        @cache_async[type(dict)](fname, model, {})
        async def func():
            return model

        assert not fname.exists()
        func.reset_cache()
