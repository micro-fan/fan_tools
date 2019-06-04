from django.http import Http404
from django.core.exceptions import PermissionDenied

from rest_framework import exceptions
from rest_framework.views import set_rollback
from rest_framework.response import Response


def api_exception_handler(exc, context):

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        error = {}
        error['reason'] = exc.__class__.__name__
        error['status'] = exc.status_code
        error['code'] = exc.default_code
        error['message'] = exc.default_detail
        error['detail'] = exc.get_full_details()

        set_rollback()
        return Response(
            {'error': error},
            status=exc.status_code,
            headers=headers,
        )

    return None
