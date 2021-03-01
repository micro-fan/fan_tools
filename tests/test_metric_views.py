from starlette.requests import Request
from starlette.routing import Route, Router
from starlette.testclient import TestClient

from fan_tools.container_utils import HealthView, PrometheusView


async def health_extra(request: Request):
    return {'test': 'OK'}


def prometheus_extra(request: Request):
    return ['test 1']


app = Router(
    [
        Route("/health/", endpoint=HealthView(), methods=["GET"]),
        Route("/health_extra/", endpoint=HealthView(health_extra), methods=["GET"]),
        Route("/prometheus/", endpoint=PrometheusView(), methods=["GET"]),
        Route("/prometheus_extra/", endpoint=PrometheusView(prometheus_extra), methods=["GET"]),
    ]
)

client = TestClient(app)


class TestHealth:
    def test_default(self):
        response = client.get('/health/')
        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}

    def test_extra(self):
        response = client.get('/health_extra/')
        assert response.status_code == 200
        assert response.json() == {'status': 'OK', 'test': 'OK'}


class TestPrometheus:
    def test_default(self):
        response = client.get('/prometheus/')
        assert response.status_code == 200
        assert response.content == b'up 1'

    def test_extra(self):
        response = client.get('/prometheus_extra/')
        assert response.status_code == 200
        assert response.content == b'up 1\ntest 1'
