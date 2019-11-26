import json
import logging


OMIT_ENTRIES = ['password', 'secret']


class LoggerMiddleware(object):
    log = logging.getLogger('LoggerMiddleware')

    def __init__(self, get_response):
        self.get_response = get_response

    def get_raw_data(self, request):
        pass

    def process_view(self, request, view_func, args, kwargs):
        self.log_request(request)

    def log_request(self, request):
        if request.GET or request.method in ('GET', 'DELETE'):
            data = request.GET.copy()
        elif request.POST:
            data = request.POST.copy()
        else:
            try:
                content_type = request.content_type
                if content_type == 'application/json':
                    try:
                        data = json.loads(request.body)
                    except Exception:
                        data = request.body.decode('utf8')[:3000]
                else:
                    try:
                        data = json.loads(request.body)
                    except Exception:
                        data = request.body.decode('utf8')[:3000]
            except Exception as e:
                data = '<Error: {}>'.format(e)

        if isinstance(data, dict):
            data = data.copy()
            for f in OMIT_ENTRIES:
                if f in data:
                    data[f] = '<REPLACED>'

        dct = {'meta': str(request.META), 'data': data}
        if request.FILES:
            dct['files'] = list(request.FILES.keys())
        msg = '{} {} => {}'.format(request.method, request.get_raw_uri(), json.dumps(dct))
        self.log.debug(msg)

    def __call__(self, request):
        return self.get_response(request)


class DeprecatedLoggerMiddleware(LoggerMiddleware):
    """
    Django < 1.10 compatible middleware
    """

    def __init__(self):
        pass

    def process_request(self, request):
        self.log_request(request)
