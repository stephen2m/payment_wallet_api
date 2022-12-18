import logging
import sys
from http import HTTPStatus
from typing import Union

from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def generate_error_message(response: Union[Response, JsonResponse]) -> dict:
    # Using the description's of the HTTPStatus class as error message.
    http_code_to_message = {
        v.value: v.description for v in HTTPStatus
    }

    error_payload = {
        'error': {
            'status_code': 0,
            'message': '',
            'details': [],
        }
    }
    error = error_payload['error']
    status_code = response.status_code

    error['status_code'] = status_code
    error['message'] = http_code_to_message[status_code]
    error['details'] = response.data

    return error


def core_exception_handler(exc, context):
    # Get the standard error response from DRF first
    response = exception_handler(exc, context)

    if response is not None:
        response.data = generate_error_message(response)

    return response


def server_error_handler(request: WSGIRequest):
    type_, value, traceback = sys.exc_info()
    logger.error(f'{traceback}: {value}')

    response = Response(
        data={'error': str(value)}, status=HTTP_500_INTERNAL_SERVER_ERROR
    )
    response.data = generate_error_message(response)

    return JsonResponse(data=response.data, status=response.status_code)
