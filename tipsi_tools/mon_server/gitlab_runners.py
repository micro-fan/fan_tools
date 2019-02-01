import asyncio
import logging

import gitlab

LOOP = 20
log = logging.getLogger('mon_server.gitlab_runners')


def update_gitlab_runners(gitlab_api):
    metrics = {}
    try:
        log.debug('Going to update runners state')
        runners = gitlab_api.runners.all(scope='online')
        for runner in runners:
            if runner['description'].endswith('disabled'):
                log.debug(f'Skip {runner}')
                continue
            elif runner['active']:
                k = 'ci_runner{config="%s"}' % runner['description']
                metrics[k] = 1
        log.debug(f'State was updated to {metrics}')
    except Exception:
        log.exception('During update_gitlab_runners')
    return metrics


async def update_gitlab_loop(update_metrics, params):
    """
    app = Sanic()
    mserver = MetricsServer(app)
    mserver.add_task(update_gitlab_loop, params={'url': GITLAB_URL, 'token': token})
    """
    gitlab_api = gitlab.Gitlab(url=params['url'], private_token=params['token'], api_version=4)
    while True:
        try:
            metrics = update_gitlab_runners(gitlab_api)
            update_metrics(metrics)
        except Exception:
            update_metrics({})
            log.exception('During loop')
        await asyncio.sleep(LOOP)
