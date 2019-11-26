from unittest import TestCase

from fan_tools.testing.meta import PropsMeta


class MetaCase(TestCase, metaclass=PropsMeta):
    def prop__ok(self):
        return True

    def test_simple(self):
        assert self.ok, 'Ok: {!r}'.format(self.ok)
