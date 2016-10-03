import os

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

