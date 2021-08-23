import pytest


@pytest.fixture(scope='session', autouse=True)
def local_cache():
    pass
