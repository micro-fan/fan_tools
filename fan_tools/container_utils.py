import asyncio
import pathlib
import shutil
from typing import List, Union

from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import Receive, Scope, Send


class ValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def remove_temp_folder(folder_path: pathlib.Path):
    try:
        shutil.rmtree(folder_path)
    except OSError:
        pass


def remove_temp_folder_task(folder_path: pathlib.Path):
    return BackgroundTask(remove_temp_folder, folder_path=folder_path)


def get_timeout(request_data: dict, param_name: str = "timeout", default: int = 60) -> int:
    timeout = default
    if timeout_data := request_data.get(param_name):
        try:
            timeout = int(timeout_data)
        except ValueError:
            pass
    return timeout


class BaseMetricsView:
    def __init__(self, *args):
        self.handlers = args

    async def get_default(self) -> List[str]:
        return []

    def get_response_handler(self):
        return Response

    async def get_handlers_data(self, request: Request) -> List[str]:
        data = []
        for handler in self.handlers:
            if asyncio.iscoroutinefunction(handler):
                res = await handler(request=request)
            else:
                res = handler(request=request)
            if isinstance(res, dict):
                res = [res]
            data.extend(res)
        return data

    async def get_response(self, request: Request) -> Response:
        data = await self.get_default()
        handlers_data = await self.get_handlers_data(request)
        resp_data = data + handlers_data
        return self.get_response_handler()('\n'.join(resp_data), media_type="text/plain")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "http"
        request = Request(scope, receive)
        response = await self.get_response(request=request)
        await response(scope, receive, send)


class HealthView(BaseMetricsView):
    async def get_default(self) -> dict:
        return {"status": "OK"}

    def get_response_handler(self):
        return JSONResponse

    async def get_response(self, request: Request) -> Response:
        data = await self.get_default()
        handlers_data = await self.get_handlers_data(request)
        data.update(*handlers_data)
        return self.get_response_handler()(data)


class PrometheusView(BaseMetricsView):
    async def get_default(self):
        return ["up 1"]


metric_storage = {}


class MetricStorage:
    def increment(self, metric_name: str) -> int:
        if metric_name not in metric_storage:
            metric_storage[metric_name] = 0
        if not isinstance(metric_storage[metric_name], int):
            raise ValueError('Metric not support incrementing')
        metric_storage[metric_name] += 1
        return metric_storage[metric_name]

    def get_metrics(self):
        return metric_storage

    def push(self, metric_name: str, value: Union[str, int, float]) -> Union[str, int, float]:
        if metric_name not in metric_storage:
            metric_storage[metric_name] = []
        if not isinstance(metric_storage[metric_name], list):
            raise ValueError('Metric not support pushing')
        metric_storage[metric_name].append(value)
        return metric_storage[metric_name]

    def reset(self):
        metric_storage.clear()
