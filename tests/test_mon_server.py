from unittest.mock import patch

import aiohttp
import pytest

from fan_tools.mon_server import MetricsServer

pytestmark = pytest.mark.asyncio


@pytest.fixture
def server_port(unused_tcp_port_factory):
    yield unused_tcp_port_factory()


@pytest.fixture
def sanic_app():
    from sanic import Sanic

    yield Sanic()


class MetricHook:
    def __init__(self):
        self.names = {}

    async def remember_update(self, update_func):
        self.update_func = update_func

    def push_metrics(self, dct):
        self.update_func(dct)


@pytest.fixture
def mhook():
    yield MetricHook()


@pytest.fixture
def mserver(sanic_app, mhook):
    server = MetricsServer(sanic_app, 'running')
    server.add_task(mhook.remember_update)
    yield server


@pytest.fixture
def patch_loop(event_loop):
    with patch('asyncio.get_event_loop') as m:
        m.return_value = event_loop


@pytest.fixture
async def running_server(sanic_app, mserver, server_port, patch_loop, event_loop):
    running_server = sanic_app.create_server(
        host='localhost', port=server_port, return_asyncio_server=True
    )
    yield await running_server
    running_server.close()


@pytest.fixture
async def get_metrics(running_server, server_port):
    async with aiohttp.ClientSession() as cli:

        async def async_get():
            resp = await cli.get(f'http://localhost:{server_port}/metrics')
            assert resp.status == 200
            return await resp.text()

        yield async_get


@pytest.fixture
def expect_metrics(get_metrics):
    async def inner_expect(expected_metrics={}):
        resp = await get_metrics()
        resp_dict = {}
        for l in resp.split('\n'):
            if not l:
                continue
            k, v = l.split(' ')
            resp_dict[k] = int(v)
        assert resp_dict == expected_metrics

    yield inner_expect


async def test_01(expect_metrics, mhook):
    await expect_metrics({'running': 1})

    mhook.push_metrics({'a': 1})
    await expect_metrics({'a': 1, 'running': 1})

    mhook.push_metrics({'b': 1})
    await expect_metrics({'a': 0, 'b': 1, 'running': 1})
