from unittest.mock import patch

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from fan_tools.mon_server import MetricsServer


pytestmark = pytest.mark.asyncio


@pytest.fixture
def server_port(unused_tcp_port_factory):
    yield unused_tcp_port_factory()


@pytest.fixture
async def fastapi_app():
    yield FastAPI()


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
def mserver(fastapi_app, mhook):
    server = MetricsServer(fastapi_app, 'running')
    server.add_task(mhook.remember_update)
    yield server


@pytest.fixture
def patch_loop(event_loop):
    with patch('asyncio.get_event_loop') as m:
        m.return_value = event_loop


@pytest.fixture
async def running_server(fastapi_app, mserver, server_port, patch_loop, event_loop):
    async with LifespanManager(fastapi_app):
        yield fastapi_app


@pytest.fixture
async def get_metrics(running_server, server_port):
    async with AsyncClient(app=running_server) as cli:
        # with TestClient(running_server) as cli:
        async def async_get():
            resp = await cli.get(f'http://localhost:{server_port}/metrics')
            assert resp.status_code == 200
            return resp.text

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
