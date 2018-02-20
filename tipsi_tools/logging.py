import os
import logging.config

from pythonjsonlogger.jsonlogger import JsonFormatter


class JSFormatter(JsonFormatter):
    msg_keys = [
        'asctime',
        'created',
        'filename',
        'funcName',
        'levelname',
        'levelno',
        'lineno',
        'module',
        'msecs',
        'message',
        'name',
        'pathname',
        'process',
        'processName',
        'relativeCreated',
        'thread',
        'threadName'
    ]


    def __init__(self, *args, env_vars=[], **kwargs):
        super(JSFormatter, self).__init__(*args, **kwargs)
        self.default_keys = {k: v for k, v in list(os.environ.items()) if k in env_vars}
        self._required_fields.extend(self.msg_keys)

    def process_log_record(self, rec):
        rec.update(self.default_keys)
        return rec


def base_handler(filename, **params):
    return {
        'level': 'DEBUG',
        'class': 'safe_logger.TimedRotatingFileHandlerSafe',
        'when': 'midnight',
        'backupCount': 30,
        'formatter': 'standard',
        'filename': filename,
        **params,
    }


def get_plain_logname(base_name, root_dir, enable_json):
    """
    we nest all plain logs to prevent double log shipping
    """
    if enable_json:
        nested_dir = os.path.join(root_dir, 'plain')
        if os.path.exists(root_dir) and not os.path.exists(nested_dir):
            os.mkdir(nested_dir)
        root_dir = nested_dir
    return os.path.join(root_dir, '{}.log'.format(base_name))


def setup_logger(base_name, root_dir=None, enable_json=True):
    if not root_dir:
        root_dir = os.environ.get('LOG_DIR')
    assert root_dir, 'You should pass root_dir parameter or set env LOG_DIR'

    JSON_FORMATTER = {
        '()': 'tipsi_tools.logging.JSFormatter',
        'env_vars': ['HOST_TYPE', 'TIPSI_CONFIG', 'TIPSI_BRANCH', 'CONTAINER_TYPE'],
    }

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': JSON_FORMATTER,
            'standard': {'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'},
        },
        'handlers': {
            'default': base_handler(get_plain_logname(base_name, root_dir, enable_json)),
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'boto3': {'level': 'INFO', },
            'botocore': {'level': 'INFO', },
            'kazoo': {'level': 'INFO', },
            'urllib3': {'level': 'INFO', }
        }
    }
    if enable_json:
        LOGGING['handlers']['json'] = base_handler(os.path.join(root_dir, '{}.json_log'.format(base_name)),
                                                   formatter='json')
        LOGGING['loggers']['']['handlers'].append('json')
    logging.config.dictConfig(LOGGING)
