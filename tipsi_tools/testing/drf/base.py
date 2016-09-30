import logging
from contextlib import contextmanager

from django.test import TestCase
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from tipsi_tools.testing.meta import PropsMeta


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

    def is_empty(self, name):
        return not hasattr(self, name)

    def create_user(self, username, groups=[], permissions=[]):
        pwd = username
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
        if not client:
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
    def client(self, client_name, default=None):
        old_client = self.default_client
        if default is not None and client_name is None:
            self.default_client = default
        else:
            self.default_client = client_name

        try:
            yield
        finally:
            self.default_client = old_client

    @contextmanager
    def cclient(self, client_name, default=None):
        old_client = self.default_client
        if default is not None and client_name is None:
            self.default_client = default
        else:
            self.default_client = client_name

        try:
            yield
        finally:
            self.default_client = old_client
