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


def setup_logger(root_dir, base_name, enable_json=True):
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
            'default': {
                'level': 'DEBUG',
                'class': 'safe_logger.TimedRotatingFileHandlerSafe',
                'filename': os.path.join(root_dir, '{}.log'.format(base_name)),
                'when': 'midnight',
                'backupCount': 30,
                'formatter': 'standard',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'DEBUG',
                'propagate': True,
            },
        }
    }
    if enable_json:
        LOGGING['handlers']['json'] = {
            'formatter': 'json',
            'level': 'DEBUG',
            'class': 'safe_logger.TimedRotatingFileHandlerSafe',
            'filename': os.path.join(root_dir, '{}_json.log'.format(base_name)),
            'when': 'midnight',
            'backupCount': 30,
        }
        LOGGING['loggers']['']['handlers'].append('json')
    logging.config.dictConfig(LOGGING)

