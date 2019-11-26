from typing import Any, Dict, Type

import pytest

from django.views import View
from fan_tools.drf.validation import validate_request
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

URL = '/myurl'


def get_assigned_request_attrs(view) -> Dict[str, Any]:
    request_attrs = {}
    if hasattr(view, 'validated_query_params'):
        request_attrs['validated_query_params'] = view.validated_query_params
    if hasattr(view, 'validated_data'):
        request_attrs['validated_data'] = view.validated_data
    return request_attrs


@pytest.fixture()
def req_factory():
    yield APIRequestFactory()


@pytest.fixture()
def apiview_cls():
    class MyAPIView(APIView):
        def get(self, request):
            return Response(status=status.HTTP_200_OK, data=get_assigned_request_attrs(self))

        def post(self, request):
            return Response(status=status.HTTP_200_OK, data=get_assigned_request_attrs(self))

    yield MyAPIView


@pytest.fixture()
def viewset_cls():
    class MyViewSet(ViewSet):
        def list(self, request):
            return Response(status=status.HTTP_200_OK, data=get_assigned_request_attrs(self))

        def create(self, request):
            return Response(status=status.HTTP_200_OK, data=get_assigned_request_attrs(self))

    yield MyViewSet


def test_no_error_if_no_data_is_passed_and_no_serializers_defined(
    req_factory: APIRequestFactory, apiview_cls: Type[APIView]
):
    apiview_cls.get = validate_request()(apiview_cls.get)
    request = req_factory.get(URL)
    assert apiview_cls.as_view()(request).status_code == 200


def test_can_only_be_used_on_class_based_apiviews(req_factory: APIRequestFactory):
    request = req_factory.get(URL)
    with pytest.raises(TypeError, match='cannot be used on function-based views'):

        @validate_request()
        def my_view(request):
            pass

        my_view(request)

    request = req_factory.get(URL)
    with pytest.raises(TypeError, match='can only be used on methods of APIView'):

        class MyView(View):
            @validate_request()
            def get(self, request):
                pass

        MyView.as_view()(request)


def test_raises_400_if_query_params_are_invalid(
    req_factory: APIRequestFactory, apiview_cls: Type[APIView]
):
    apiview_cls.get = validate_request(
        query_params={'username': serializers.CharField(allow_blank=False, required=True)}
    )(apiview_cls.get)

    response = apiview_cls.as_view()(req_factory.get(URL))
    assert response.status_code == 400

    response = apiview_cls.as_view()(req_factory.get(URL, data={}))
    assert response.status_code == 400

    response = apiview_cls.as_view()(req_factory.get(URL, data={'username': ''}))
    assert response.status_code == 400


def test_raises_400_if_data_is_invalid(req_factory: APIRequestFactory, apiview_cls: Type[APIView]):
    apiview_cls.post = validate_request(
        data={'username': serializers.CharField(allow_blank=False, required=True)}
    )(apiview_cls.post)

    response = apiview_cls.as_view()(req_factory.post(URL))
    assert response.status_code == 400

    response = apiview_cls.as_view()(req_factory.post(URL, data={}))
    assert response.status_code == 400

    response = apiview_cls.as_view()(req_factory.post(URL, data={'username': ''}))
    assert response.status_code == 400


def test_raises_400_if_data_is_invalid_as_serializer(
    req_factory: APIRequestFactory, apiview_cls: Type[APIView]
):
    class MySerializer(serializers.Serializer):
        username = serializers.CharField(allow_blank=False, required=True)

    apiview_cls.post = validate_request(data=MySerializer)(apiview_cls.post)

    response = apiview_cls.as_view()(req_factory.post(URL))
    assert response.status_code == 400

    response = apiview_cls.as_view()(req_factory.post(URL, data={}))
    assert response.status_code == 400

    response = apiview_cls.as_view()(req_factory.post(URL, data={'username': ''}))
    assert response.status_code == 400


def test_has_query_params_if_passed_and_valid(
    req_factory: APIRequestFactory, apiview_cls: Type[APIView]
):
    apiview_cls.get = validate_request(
        query_params={'username': serializers.CharField(allow_blank=False, required=True)}
    )(apiview_cls.get)

    response = apiview_cls.as_view()(req_factory.get(URL, data={'username': 'maksim'}))
    assert response.status_code == 200
    assert response.data['validated_query_params']['username'] == 'maksim'
    assert 'validated_data' not in response.data


def test_has_data_if_passed_and_valid(req_factory: APIRequestFactory, apiview_cls: Type[APIView]):
    apiview_cls.post = validate_request(
        data={'username': serializers.CharField(allow_blank=False, required=True)}
    )(apiview_cls.post)

    response = apiview_cls.as_view()(req_factory.post(URL, data={'username': 'maksim'}))
    assert response.status_code == 200
    assert response.data['validated_data']['username'] == 'maksim'
    assert 'validated_query_params' not in response.data


def test_400_for_invalid_data_on_viewsets(req_factory: APIRequestFactory, viewset_cls: ViewSet):
    viewset_cls.list = validate_request(
        query_params={'username': serializers.CharField(allow_blank=False, required=True)}
    )(viewset_cls.list)

    request = req_factory.get(URL, data={'username': ''})
    response = viewset_cls.as_view({'get': 'list'})(request)
    assert response.status_code == 400


def test_valid_query_params_on_viewsets(req_factory: APIRequestFactory, viewset_cls: ViewSet):
    viewset_cls.list = validate_request(
        query_params={'username': serializers.CharField(allow_blank=False, required=True)}
    )(viewset_cls.list)

    request = req_factory.get(URL, data={'username': 'maksim'})
    response = viewset_cls.as_view({'get': 'list'})(request)
    assert response.status_code == 200
    assert response.data['validated_query_params']['username'] == 'maksim'
    assert 'validated_data' not in response.data


def test_valid_data_on_viewsets(req_factory: APIRequestFactory, viewset_cls: ViewSet):
    viewset_cls.create = validate_request(
        data={'username': serializers.CharField(allow_blank=False, required=True)}
    )(viewset_cls.create)

    request = req_factory.post(URL, data={'username': 'maksim'})
    response = viewset_cls.as_view({'post': 'create'})(request)
    assert response.status_code == 200
    assert response.data['validated_data']['username'] == 'maksim'
    assert 'validated_query_params' not in response.data
