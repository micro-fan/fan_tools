#!/usr/bin/env python3
"""
Export items in prometheus format.
"""
import asyncio
import logging
import os
from collections import ChainMap
from functools import partial

from fastapi import APIRouter, FastAPI
from fastapi.responses import PlainTextResponse


log = logging.getLogger('fan_monitoring')
router = APIRouter()


class MetricsServer:
    """
    You you should add monitoring functions with add_task
    Your update function will receive update_metrics function with all additional args
    """

    def __init__(self, app: FastAPI, status_metric='running{example_var="default_env"}'):
        self.app = app
        self.app.get('/metrics', response_class=PlainTextResponse)(self.expose_metrics)
        self.metrics = f'{status_metric} 1'
        self.all_names = [{status_metric: 1}]
        self.tasks = []
        self.running_tasks = []

    def update_metrics(self, names, metrics):
        for name in names:
            if name not in metrics:
                names[name] = 0

        for name, value in metrics.items():
            names[name] = value

        mlist = [f'{name} {value}' for name, value in ChainMap(*self.all_names).items()]
        self.metrics = '\n'.join(mlist)
        return names

    def gen_update_func(self):
        local_names = {}
        self.all_names.append(local_names)
        return partial(self.update_metrics, local_names)

    def add_task(self, loop_func, *args, **kwargs):
        self.tasks.append({'func': loop_func, 'args': args, 'kwargs': kwargs})
        self.app.on_event('startup')(self.run_tasks)

    async def run_tasks(self):
        print(f'RUN TASKS: {self.tasks}')
        for task in self.tasks:
            loop_func = task['func']
            coro = loop_func(self.gen_update_func(), *task['args'], **task['kwargs'])
            self.running_tasks.append(asyncio.create_task(coro))

    async def finish_tasks(self):
        for task in self.runing_tasks:
            await task.cancel()

    async def expose_metrics(self):
        return self.metrics


def main():
    import uvicorn

    from fan_tools.mon_server.certs import update_certs_loop

    app = FastAPI()
    mserver = MetricsServer(app)
    mserver.add_task(update_certs_loop, hosts=['perfectlabel.io', 'robopickles.com'])
    uvicorn.run(app, host='0.0.0.0', port=os.environ.get('MONITORING_PORT', 8000))


if __name__ == '__main__':
    main()
