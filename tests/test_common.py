import pytest
from fan_tools.django.fields import ChoicesEnum
from fan_tools.python import usd_round, dict_contains, slide, expand_dot


@pytest.fixture(scope='class')
def local_cache():
    pass


@pytest.fixture
def session_settings():
    pass


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


def test_04_dict_contains():
    a = {'key': 'aa', 'msg': {'bb': 1, 'cc': True}}
    b = {'key': 'aa', 'msg': {'bb': 2, 'cc': True}}

    assert dict_contains(a, {'key': 'aa'})
    assert dict_contains(b, {'key': 'aa'})
    assert dict_contains(a, {'msg': {'bb': 1}})
    assert dict_contains(b, {'msg': {'bb': 2}})

    assert not dict_contains(a, {'msg': {'bb': 2}})
    assert not dict_contains(b, {'msg': {'bb': 1}})

    assert dict_contains(a, {'msg': {'bb': 1, 'cc': True}})
    assert dict_contains(b, {'msg': {'bb': 2, 'cc': True}})

    assert not dict_contains(a, {'msg': {'bb': 1, 'cc': False}})
    assert not dict_contains(b, {'msg': {'bb': 2, 'cc': False}})
    assert not dict_contains(a, {'msg': {'bb': 1, 'nested': []}})


def test_05_expand_dot():
    assert expand_dot({'msg.payload.status': 'waiting_release'}) == {
        'msg': {'payload': {'status': 'waiting_release'}}
    }


def test_06_slide():
    assert list(slide(range(3))) == [(0, 1), (1, 2), (2, None)]
