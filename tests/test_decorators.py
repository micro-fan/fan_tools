import json
from pathlib import Path
from unittest.mock import MagicMock

from fan_tools.python import cache_async, memoize


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


class TestMemoize:
    memoized = '{"ab82775f76a7c30b94db389aa2e8702f": "{\\"args\\": [\\"a\\"], \\"kwargs\\": {\\"name\\": \\"b\\"}}"}'

    def test_01_basic(self, tmp_path):
        fname = tmp_path / '.cache/memoized_test.json'

        @memoize(fname)
        def func(*args, **kwargs):
            return json.dumps(
                {
                    'args': args,
                    'kwargs': kwargs,
                }
            )

        assert not fname.exists()
        func('a', name='b')
        assert fname.exists()
        assert fname.read_text() == self.memoized

        func.reset_cache()
        assert not fname.exists()

    def test_02_no_params(self):
        fname = Path('.cache/memoized.json')
        if fname.exists():
            fname.unlink()

        @memoize
        def func(*args, **kwargs):
            return json.dumps(
                {
                    'args': args,
                    'kwargs': kwargs,
                }
            )

        assert not fname.exists()
        func('a', name='b')
        assert fname.exists()
        assert fname.read_text() == self.memoized

        func.reset_cache()
        assert not fname.exists()
