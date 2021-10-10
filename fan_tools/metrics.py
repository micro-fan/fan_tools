"""
check usage in examples/send_dd_metric.py
"""

import logging
import os


metric_logger = logging.getLogger('fan.metric')
ENV = os.environ.get('ENV', 'not_set')
SERVICE = os.environ.get('SERVICE', 'not_set')
COMMON = {
    'env': ENV,
    'service': SERVICE,
}
if version := os.environ.get('GITHUB_SHA'):
    COMMON['version'] = version


def send_error_metric(name: str, tags={}, increment=1):
    """
    Shortcut to bypass all fuss with monitoring, just call when things must not happen
    Usually you want to setup some kind of notification for such metric
    """
    metric_logger.error(
        {
            'tags': {
                **COMMON,
                **tags,
                'error_type': name,
            },
            'increment': increment,
            'message': 'error_metric',
        }
    )


def send_metric(name: str, tags={}, increment=1):
    metric_logger.info(
        {
            'tags': {
                **COMMON,
                **tags,
            },
            'message': name,
            'increment': increment,
        }
    )
