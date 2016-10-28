import json
import logging


class LoggerMiddleware(object):
    log = logging.getLogger('LoggerMiddleware')

    def __init__(self, get_response):
        self.get_response = get_response

    def log_request(self, request):
        try:
            data = request.body.decode('utf8')[:3000]
        except Exception as e:
            data = '<Error: {}>'.format(e)
        dct = {'meta': str(request.META),
               'data': data}
        msg = '{} {} => {}'.format(request.method, request.get_raw_uri(), json.dumps(dct))
        self.log.debug(msg)

    def __call__(self, request):
        self.log_request(request)
        return self.get_response(request)


class DeprecatedLoggerMiddleware(LoggerMiddleware):
    '''
    Django < 1.10 compatible middleware
    '''
    def __init__(self):
        pass

    def process_request(self, request):
        self.log_request(request)
