import json

from unittest import mock
from rest_framework import status


class MockResponse:
    def __init__(self, json_content, status_code):
        self.json_content = json_content
        self.status_code = status_code

    def json(self, **params):
        return self.json_content

    @property
    def content(self):
        return json.dumps(self.json_content)


class MockGet:
    target = 'requests.get'

    @classmethod
    def mock(cls, result, status_code=status.HTTP_200_OK):
        """
        Patch requests.get method to always return specified response
        """
        def deco(fun):
            def new_fun(*args, **kwargs):
                def get_results(*inner_args, **inner_kwargs):
                    if callable(result):
                        self = args[0]
                        r = result(self)
                        return MockResponse(r, status_code)
                    else:
                        return MockResponse(result, status_code)

                patcher, m = cls.get_patcher(get_results)
                patcher.start()
                try:
                    ans = fun(mock_obj=m, *args, **kwargs)
                finally:
                    patcher.stop()
                return ans
            return new_fun
        return deco

    @classmethod
    def get_patcher(cls, side_effect):
        m = mock.Mock(side_effect=side_effect)
        return mock.patch(cls.target, m), m


class MockPost(MockGet):
    target = 'requests.post'


class MockPatch(MockGet):
    target = 'requests.patch'


class MockPut(MockGet):
    target = 'requests.put'


class MockDelete(MockGet):
    target = 'requests.delete'
