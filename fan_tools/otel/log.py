import logging
import os
import socket
from contextlib import suppress
from pathlib import Path

from fan_tools import const
from fan_tools.fan_logging import setup_logger


default_log_dir = os.environ.get('LOG_DIR', '.logs')
log_file_name = os.environ.get('LOG_FILE_NAME', 'fan_logging')


def enable_otel_logger(
    log_dir=default_log_dir,
    log_file=log_file_name,
    vector_info=None,
    env_vars=const.ENV_VARS,
    log_levels=const.LOG_LEVELS,
):
    log_dir = Path(default_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers = {}
    if vector_info is None:
        vector_info = const.OTEL['VECTOR']

    with suppress(socket.gaierror):
        socket.gethostbyname(vector_info[0])
        handlers = {
            'vector': {
                'level': 'DEBUG',
                'class': 'fan_tools.fan_logging.handlers.SysLogHandler',
                'address': vector_info,
                'formatter': 'json',
            }
        }

    params = {
        'root_dir': log_dir,
        'enable_stdout': True,
        'stdout_level': 'INFO',
        'json_formatter': 'fan_tools.fan_logging.JSFormatter',
        'handlers': handlers,
    }

    params['json_formatter'] = 'fan_tools.otel.OtelJSFormatter'
    params['enable_stdout'] = False
    params['stdout_level'] = 'CRITICAL'
    params['json_params'] = {
        'env_vars': env_vars,
    }

    with suppress(ValueError):
        setup_logger(log_file, **params)

    for level, names in log_levels.items():
        for name in names:
            logging.getLogger(name).setLevel(level)
