from django.http import QueryDict
from rest_framework.views import APIView


def use_form(form_class, request=None, **top_kwargs):
    """
    Validate request (query_params or request body with args from url) with serializer and pass
    validated data dict to the view function instead of request object.
    """

    def validated_form(request, **kwargs):
        # import ipdb; ipdb.set_trace()
        data = request.query_params.dict() if request.method in ['GET'] else request.data
        if isinstance(data, QueryDict):
            form = form_class(data={**data.dict(), **kwargs})
        elif isinstance(data, dict):
            form = form_class(data={**data, **kwargs})
        else:
            form = form_class(data=data, **kwargs)
        form.is_valid(raise_exception=True)
        return form

    if request:
        kwargs = {}
        if request.resolver_match:
            kwargs = {**request.resolver_match.kwargs}
        if top_kwargs:
            kwargs = {**kwargs, **top_kwargs}

        return validated_form(request, **kwargs).validated_data

    def wrap(func):
        def method_wrap(view, request, *args, **kwargs):
            form = validated_form(request, **kwargs)
            if hasattr(view, 'log'):
                form.log = view.log
            return func(view, form.validated_data, *args, **kwargs)

        def function_wrap(request, *args, **kwargs):
            form = validated_form(request, **kwargs)
            return func(form.validated_data, *args, **kwargs)

        def inner(*args, **kwargs):
            is_method = isinstance(args[0], APIView)
            return (method_wrap if is_method else function_wrap)(*args, **kwargs)

        return inner

    return wrap
