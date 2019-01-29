#!/usr/bin/env python3
"""
Export items in prometheus format.
"""
import logging
import os
from collections import ChainMap
from functools import partial

from sanic import Sanic, response

log = logging.getLogger('tipsi_monitoring')


class MetricsServer:
    """
    You you should add monitoring functions with add_task
    Your update function will receive update_metrics function with all additional args
    """
    def __init__(self, app, status_metric='running{example_var="default_env"}'):
        self.app = app
        self.app.add_route(self.expose_metrics, '/metrics')
        self.metrics = f'{status_metric} 1'
        self.all_names = [{status_metric: 1}]

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
        self.app.add_task(loop_func(self.gen_update_func(), *args, **kwargs))

    async def expose_metrics(self, request):
        return response.text(self.metrics)


def main():
    from tipsi_tools.mon_server.certs import update_certs_loop
    app = Sanic()
    mserver = MetricsServer(app)
    mserver.add_task(update_certs_loop, hosts=['gettipsi.com', 'proofnetwork.io'])
    app.run(host='0.0.0.0', port=os.environ.get('MONITORING_PORT'))


if __name__ == '__main__':
    main()
