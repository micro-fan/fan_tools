import pytest

from fan_tools.django.fields import ChoicesEnum
from fan_tools.python import (
    areduce,
    chunks,
    dict_contains,
    dot_get,
    expand_dot,
    retry,
    slide,
    usd_round,
)


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


@pytest.mark.asyncio
async def test_07_async_reduce():
    async def sum_two(a, b):
        return a + b

    assert await areduce(sum_two, [1, 2, 3, 4, 5]) == 15
    assert await areduce(sum_two, [1, 2, 3, 4, 5], initial=100) == 115


def test_08_chunks():
    cases = [
        # test common case
        (list(range(0, 4)), 2, [[0, 1], [2, 3]]),
        # test common case for another n
        (list(range(0, 9)), 3, [[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
        # some cases
        (list(range(0, 10)), 3, [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]),
        (list(range(0, 11)), 3, [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10]]),
        # test empty list
        ([], 3, []),
        # test length of list < n
        ([1], 3, [[1]]),
        # test tuple
        ((1, 2, 3, 4, 5, 6), 3, [(1, 2, 3), (4, 5, 6)]),
    ]

    for to_chunks, n, result in cases:
        assert list(chunks(to_chunks, n)) == result


def test_09_retry(capfd):
    @retry(tries=3)
    def func_to_retry():
        print(1)
        raise Exception

    with pytest.raises(Exception):
        func_to_retry()

    out, err = capfd.readouterr()
    assert out == '1\n1\n1\n'


@pytest.mark.asyncio
async def test_09_retry_async(capfd):
    @retry(tries=3)
    async def func_to_retry():
        print(1)
        raise Exception

    with pytest.raises(Exception):
        await func_to_retry()

    out, err = capfd.readouterr()
    assert out == '1\n1\n1\n'


def test_10_retry(capfd):
    @retry(ValueError, tries=3)
    def func_to_retry():
        print(1)
        raise ValueError

    with pytest.raises(ValueError):
        func_to_retry()

    out, err = capfd.readouterr()
    assert out == '1\n1\n1\n'


@pytest.mark.asyncio
async def test_10_retry_async(capfd):
    @retry(ValueError, tries=3)
    async def func_to_retry():
        print(1)
        raise ValueError

    with pytest.raises(ValueError):
        await func_to_retry()

    out, err = capfd.readouterr()
    assert out == '1\n1\n1\n'


def test_11_retry(capfd):
    @retry(tries=3)
    def func_to_retry():
        print(1)

    func_to_retry()

    out, err = capfd.readouterr()
    assert out == '1\n'


@pytest.mark.asyncio
async def test_11_retry_async(capfd):
    @retry(tries=3)
    async def func_to_retry():
        print(1)

    await func_to_retry()

    out, err = capfd.readouterr()
    assert out == '1\n'


def test_12_retry(capfd):
    class A:
        @retry(tries=3)
        def func_to_retry(self):
            print(1)

    A().func_to_retry()

    out, err = capfd.readouterr()
    assert out == '1\n'


@pytest.mark.asyncio
async def test_12_retry_async(capfd):
    class A:
        @retry(tries=3)
        async def func_to_retry(self):
            print(1)

    await A().func_to_retry()

    out, err = capfd.readouterr()
    assert out == '1\n'


def test_13_retry(capfd):
    class A:
        @retry(tries=3)
        def func_to_retry(self, a, b):
            print(a, b)

    A().func_to_retry('111', b='222')

    out, err = capfd.readouterr()
    assert out == '111 222\n'


@pytest.mark.asyncio
async def test_13_retry_async(capfd):
    class A:
        @retry(tries=3)
        async def func_to_retry(self, a, b):
            print(a, b)

    await A().func_to_retry('111', b='222')

    out, err = capfd.readouterr()
    assert out == '111 222\n'


def test_14_dot_get():
    d = {'a': {'b': {'c': [1]}}}
    assert dot_get('a.b.c', d) == [1]
    assert dot_get('a*b*c', d, sep='*') == [1]
    assert dot_get('a*b*c*d', d, sep='*', default=[2]) == [2]
    assert dot_get('a*b*d', d, sep='*', default=[123]) == [123]

    d1 = {'a': None}
    assert dot_get('a.b', d1) is None
    assert dot_get('a.b', d1, None) is None
