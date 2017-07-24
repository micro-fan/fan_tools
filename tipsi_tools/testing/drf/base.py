import logging
from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from tipsi_tools.testing.meta import PropsMeta


def get_ids(data, path='id'):
    if isinstance(data, list):
        for item in data:
            yield from get_ids(item, path)
    elif isinstance(data, dict):
        part, *rest = path.split('.', 1)
        if rest:
            if part in data:
                yield from get_ids(data.get(part), rest[0])
        else:
            yield data.get(part)
    else:
        yield None


class BaseTest(TestCase, metaclass=PropsMeta):
    log = logging.getLogger('BaseTest')
    content_format = 'json'
    default_client = 'c'

    _overridden_settings = {
        'DEFAULT_FILE_STORAGE': 'django.core.files.storage.FileSystemStorage',
        'BROKER_BACKEND': 'memory',
        'CACHES': {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'TIMEOUT': 60 * 15
            }
        }
    }

    @classmethod
    def setUpTestData(cls):
        # Cache all methods decorated with class_prop
        # before running any test from test case
        for name in dir(cls):
            getattr(cls, name)

    def is_empty(self, name):
        return not hasattr(self, name)

    @classmethod
    def create_user(cls, username, groups=(), permissions=()):
        pwd = username
        User = get_user_model()
        exists = User.objects.filter(username=username).first()
        if exists:
            user = exists
        else:
            user = User.objects.create_user(username, '%s@gettipsi.com' % username, pwd)
            for name in groups:
                group = Group.objects.filter(name=name).first()
                if not group:
                    group = Group.objects.create(name=name)
                user.groups.add(group)

            for model, codename in permissions:
                content_type = ContentType.objects.get_for_model(model)
                try:
                    p = Permission.objects.get(codename=codename, content_type=content_type)
                except Permission.DoesNotExist:
                    p = Permission.objects.create(codename=codename, content_type=content_type)
                user.user_permissions.add(p)
        client = APIClient()
        client.login(username=username, password=pwd)

        # refresh permissions
        user.refresh_from_db()
        user.client = client
        return user

    def prop__u(self):
        return self.create_user('simple_user')

    def prop__c(self):
        ''' Authorized client '''
        return self.create_user('authorized', [], [])

    def prop__c2(self):
        ''' Unauthorized client '''
        return APIClient()

    def prop__superuser(self):
        User = get_user_model()
        exists = User.objects.filter(username='su').first()
        if exists:
            return exists
        return User.objects.create_superuser('su', 'su@u.com', 'su')

    def prop__su(self):
        self.superuser
        su = APIClient()
        su.login(username='su', password='su')
        self.superuser.client = su
        return self.superuser

    def _method(self, method, url, data, client):
        User = get_user_model()
        if not client:
            if isinstance(self.default_client, User):
                client = self.default_client
            else:
                client = getattr(self, self.default_client)
        if isinstance(client, User):
            client = client.client
        return getattr(client, method)(url, data, format=self.content_format)

    def post(self, url, data, client=None):
        return self._method('post', url, data, client)

    def patch(self, url, data, client=None):
        return self._method('patch', url, data, client)

    def put(self, url, data, client=None):
        return self._method('put', url, data, client)

    def get(self, url, data={}, client=None):
        return self._method('get', url, data, client)

    def delete(self, url, data={}, client=None):
        return self._method('delete', url, data, client)

    def json_method(self, method, *args, **kwargs):
        cf = self.content_format
        self.content_format = 'json'
        r = getattr(self, method)(*args, **kwargs)
        self.content_format = cf
        return r

    def get_json(self, *args, **kwargs):
        r = self.json_method('get', *args, **kwargs)
        assert r.status_code == 200, r.status_code
        return r.json()

    def get_results(self, *args, **kwargs):
        return self.get_json(*args, **kwargs)['results']

    def post_json(self, *args, **kwargs):
        r = self.json_method('post', *args, **kwargs)
        assert r.status_code == 201, (r.status_code, r.content)
        return r.json()

    def patch_json(self, *args, **kwargs):
        r = self.json_method('patch', *args, **kwargs)
        assert r.status_code == 200, (r.status_code, r.content)
        return r.json()

    def put_json(self, *args, **kwargs):
        r = self.json_method('put', *args, **kwargs)
        assert r.status_code == 200, r.status_code
        return r.json()

    def delete_json(self, *args, **kwargs):
        r = self.json_method('delete', *args, **kwargs)
        assert r.status_code == 204, r.status_code
        assert not r.content, r.content

    @contextmanager
    def set_client(self, client):
        """
        temporary change default client for REST queries
        you can use string name or User instance as a client
        """
        old_client = self.default_client
        try:
            self.default_client = client
            yield
        finally:
            self.default_client = old_client

    def assert_items(self, expected, data, path='id'):
        """
        Extract item from `data` by `path` and compare with `expected` items
        :param expected: List of expected items.
        :param data: Tested data
        :param path: Path to the item
        Usage:
        >>> self.assert_items((1, 3, 5, 8), [
        ...     {
        ...         'name': 'bob',
        ...         'wines': [
        ...             {'name': 'wine1', 'attributes': [
        ...                 {'color': 'red', 'id': 1},
        ...                 {'color': 'green', 'id': 5},
        ...             ]},
        ...             {'name': 'wine2', 'attributes': [
        ...                 {'color': 'red', 'id': 3},
        ...             ]},
        ...         ]
        ...     },
        ...     {
        ...         'name': 'bob',
        ...         'wines': [
        ...             {'name': 'wine3', 'attributes': [
        ...                 {'color': 'red', 'id': 8},
        ...             ]},
        ...         ]
        ...     }
        ... ], 'wines.attributes.id')
        """
        actual = list(get_ids(data, path))
        assert len(expected) == len(actual), ('Expected and actual data length is not equal:\n'
                                              'len({!r}) != len({!r})'.format(expected, actual))
        assert set(expected) == set(actual), ('Expected ids are not equal to actual ids:\n'
                                              '{!r} != {!r}'.format(set(expected), set(actual)))
