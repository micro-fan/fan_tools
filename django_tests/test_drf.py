import pytest
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory


from tipsi_tools.drf import use_form


class SimpleForm(serializers.Serializer):
    test_int = serializers.IntegerField()
    test_str = serializers.CharField()


valid = {'test_int': 1, 'test_str': 'some string'}
invalid = {'test_int': 'aa', 'test_str': ''}


class FactoryWrapper(APIRequestFactory):
    def request(self, *args, **kwargs):
        return Request(super().request(*args, **kwargs))


@pytest.fixture
def request_factory():
    yield FactoryWrapper()


def test_01_use_form(request_factory):
    out = use_form(SimpleForm, request_factory.get('', valid))
    assert out == valid


def test_02_use_form_validateion_error(request_factory):
    with pytest.raises(ValidationError) as e:
        use_form(SimpleForm, request_factory.get('', invalid))
    assert e.value.detail == {'test_int': ['A valid integer is required.'],
                              'test_str': ['This field may not be blank.']}


@use_form(SimpleForm)
def decorated(data):
    return data


def test_03_decorator(request_factory):
    out = decorated(request_factory.get('', valid))
    assert out == valid
    with pytest.raises(ValidationError) as e:
        decorated(request_factory.get('', invalid))
    assert e.value.detail == {'test_int': ['A valid integer is required.'],
                              'test_str': ['This field may not be blank.']}
