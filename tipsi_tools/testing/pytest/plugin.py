import pytest

from tipsi_tools.testing.pytest import client_fixtures
from tipsi_tools.testing.pytest.client_fixtures import UserWrapper
from tipsi_tools.testing.pytest.django_fixtures import (  # noqa
    session_settings, module_settings,
    module_transaction, function_fixture, module_fixture
)


def vprint_func(*args, **kwargs):
    pass


@pytest.fixture(scope='session')
def vprint():
    yield vprint_func


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    from django.conf import settings
    settings.TESTING = True
    verbose = config.getoption('verbose')
    settings.PYTEST_VERBOSE = verbose
    if verbose:
        global vprint_func
        vprint_func = print


def pytest_unconfigure(config):
    from django.conf import settings
    settings.TESTING = False


def pytest_addoption(parser):
    group = parser.getgroup('docme')
    group.addoption('--write-docs', action='store_true', default=False,
                    help='Write http requests for documentation')


def setup_docs_logger(item):
    func = item.function
    if hasattr(func, 'docme') and item.config.getoption('write_docs'):
        client_fixtures.request_logger = client_fixtures.RequestLogger(item)


@pytest.fixture
def docs_logger():
    """
    Make requests without being logged:

    >>> def my_test(docs_logger):
    ...     with docs_logger.silent():
    ...        client.get_json(url)  # not logged
    ...     client.get_json(url)  # logged
    """
    yield client_fixtures.request_logger


def finish_docs_logger(item, nextitem):
    func = item.function
    if hasattr(func, 'docme'):
        client_fixtures.request_logger.finish()
        client_fixtures.request_logger = client_fixtures.RequestLoggerStub()


def load_fixtures_by_scope(request):
    """
    loads fixtures in order: session => module => class => function
    """
    skip_fixtures = set([request.fixturename, 'module_transaction', 'request'])
    for scope in ['session', 'module', 'class', 'function']:
        for name in set(request.fixturenames) - skip_fixtures:
            fdef = request._arg2fixturedefs[name][0]
            if fdef.scope == scope:
                request.getfixturevalue(name)
                skip_fixtures.add(name)


@pytest.fixture(autouse=True)  # noqa: F811
def auto_transaction(request):
    """
    It should be the last fixture, so we ensure that we've loaded all other required fixtures
    before open transaction.
    If we meet error here, try to modify `if` as `name not in (request.fixturename, OTHERNAME)`
    """
    if 'module_transaction' not in request.fixturenames:
        yield None
    else:
        load_fixtures_by_scope(request)
        # We cannot request module_transaction or it will be used for all our tests
        module_transaction = request.getfixturevalue('module_transaction')  # noqa: F811
        with module_transaction(request.fixturename):
            yield


def finish_unused_fixtures(item, nextitem):
    if not nextitem:
        return
    defs = item._fixtureinfo.name2fixturedefs

    skip_finishing = set(item.fixturenames) & set(nextitem.fixturenames)
    vprint_func('Skip finishing: {}'.format(skip_finishing))

    to_finish = set(item.fixturenames) - set(nextitem.fixturenames)
    for name in to_finish:
        fdef = defs[name][0]
        vprint_func('Finish fixture: {}'.format(name))
        fdef.finish()


def pytest_runtest_setup(item):
    setup_docs_logger(item)


def pytest_runtest_teardown(item, nextitem):
    finish_unused_fixtures(item, nextitem)
    finish_docs_logger(item, nextitem)


@pytest.fixture(scope='session', autouse=True)  # noqa
def local_cache(session_settings, django_db_setup):
    session_settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    session_settings.BROKER_BACKEND = 'memory'
    session_settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'TIMEOUT': 60 * 15
        }
    }
    yield session_settings


@pytest.fixture
def anonymous_client(module_transaction):
    yield UserWrapper(None)
