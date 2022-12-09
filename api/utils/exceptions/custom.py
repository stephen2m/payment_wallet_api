from django.utils.encoding import force_text
from rest_framework.exceptions import APIException


class BaseCustomException(APIException):
    status_code = None
    default_detail = None

    def __init__(self, error_message):
        self.error_message = error_message

    def to_dict(self):
        return {'error': self.error_message}


class InvalidRequest(BaseCustomException):
    status_code = 400
    default_detail = 'Invalid request'
    default_code = 'invalid_request'

    def __init__(self, detail, field=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code

        if field is not None and detail is not None:
            self.detail = {field: force_text(detail)}
        elif detail is not None:
            self.detail = {'error': force_text(detail)}
        else:
            self.detail = {'error': force_text(self.default_detail)}
