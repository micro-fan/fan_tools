import inspect
import uuid
from typing import Callable, Dict, Optional, Type, TypeVar, Union, Any

from django.http import QueryDict, HttpRequest
from rest_framework import serializers, exceptions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


_ValidationSchema = Union[
    Dict[str, serializers.Field],
    Type[serializers.Serializer]
]

_C = TypeVar('_C', bound=Callable)


def make_serializer_cls(fields_mapping: Dict[str, serializers.Field]) -> Type[serializers.Serializer]:
    cls_name = uuid.uuid4().hex + 'AnonymousSerializer'
    bases = (serializers.Serializer,)
    # noinspection PyTypeChecker
    return type(cls_name, bases, fields_mapping)


def validate_with_serializer(serializer_cls: Type[serializers.Serializer], data: Any) -> Any:
    serializer = serializer_cls(data=data)
    try:
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    except serializers.ValidationError as exc:
        raise exceptions.ParseError(exc.detail)


def validate_request_data(serializer_cls: Type[serializers.Serializer],
                          request: Union[Request, HttpRequest],
                          **top_kwargs) -> Any:
    def validated_form(request, **kwargs):
        data = request.query_params.dict() if request.method in ['GET'] else request.data
        if isinstance(data, QueryDict):
            form = serializer_cls(data={**data.dict(), **kwargs})
        elif isinstance(data, dict):
            form = serializer_cls(data={**data, **kwargs})
        else:
            form = serializer_cls(data=data, **kwargs)
        form.is_valid(raise_exception=True)
        return form

    if request:
        kwargs = {}
        if request.resolver_match:
            kwargs = {**request.resolver_match.kwargs}
        if top_kwargs:
            kwargs = {**kwargs, **top_kwargs}

        return validated_form(request, **kwargs).validated_data


class validate_request:
    def __init__(self, *,
                 query_params: Optional[_ValidationSchema] = None,
                 data: Optional[_ValidationSchema] = None
                 ) -> None:
        if isinstance(query_params, dict):
            query_params = make_serializer_cls(query_params)
        self.query_params_serializer_cls = query_params

        if isinstance(data, dict):
            data = make_serializer_cls(data)
        self.data_serializer_cls = data

    def __call__(self, method: _C) -> _C:
        _self = self

        if not inspect.getfullargspec(method).args or not inspect.getfullargspec(method).args[0] == 'self':
            # relying on convention to determine whether it's a method or a function
            raise TypeError('@validate_request cannot be used on function-based views')

        def method_wrapper(self: APIView, request: Request, *args: Any, **kwargs: Any) -> Response:
            if not isinstance(self, APIView):
                raise TypeError('@validate_request can only be used on methods of APIView')

            if hasattr(self, 'log'):
                if _self.query_params_serializer_cls:
                    _self.query_params_serializer_cls.log = self.log
                if _self.data_serializer_cls:
                    _self.data_serializer_cls.log = self.log

            if _self.query_params_serializer_cls is not None:
                self.validated_query_params = validate_with_serializer(_self.query_params_serializer_cls, request.query_params)

            if _self.data_serializer_cls is not None:
                self.validated_data = validate_with_serializer(_self.data_serializer_cls, request.data)

            return method(self, request, *args, **kwargs)

        return method_wrapper
