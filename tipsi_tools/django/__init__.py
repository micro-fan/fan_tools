from django.db import transaction

_global = {'request_id': None, 'data': {}}


def _get_request_unique_cache():
    try:
        import uwsgi
        rid = uwsgi.request_id()
        if rid != _global['request_id']:
            _global['request_id'] = rid
            _global['data'] = {}
        data = _global['data']
    except:
        data = {}

    return data


def request_uniq(func):
    """
    return unique dict for each uwsgi request.
    note: won't work on non-uwsgi cases
    """

    def _wrapped(*args, **kwargs):
        data = _get_request_unique_cache()
        return func(data, *args, **kwargs)

    return _wrapped


def _deffered_on_commit():
    return transaction.on_commit


def on_commit():
    return _deffered_on_commit()


def call_once_on_commit(func):
    key = '{}.{}_is_added_on_commit'.format(func.__module__, func.__name__)

    @request_uniq
    def _wrapped(cache, *args, **kwargs):
        if cache.get(key) is None:
            on_commit()(lambda: func(*args, **kwargs))
            cache[key] = True

    return _wrapped
