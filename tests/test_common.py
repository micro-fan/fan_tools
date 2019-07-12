import pytest
from tipsi_tools.django.fields import ChoicesEnum
from tipsi_tools.python import usd_round


@pytest.fixture
def foobar_enum():
    class FooBarEnum(ChoicesEnum):
        foo = 1
        bar = 2

    return FooBarEnum


def test_choices_enum(foobar_enum):
    expected = [(1, 'foo'), (2, 'bar')]
    choices = foobar_enum.get_choices()
    assert choices == expected, choices


def test_usd_round():
    assert str(usd_round('12.9800000003')) == '12.98'
