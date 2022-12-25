from rest_framework.exceptions import APIException


class InstantPayError(APIException):
    pass


class PaymentRequestStatusError(APIException):
    pass


class StitchConfigurationIncomplete(APIException):
    pass


class StitchClientAuthenticationError(APIException):
    pass


class BankAccountVerificationError(APIException):
    pass


class LinkPayError(APIException):
    def __init__(self, detail=None, code=None, extras=None):
        super().__init__(detail, code)

        if extras is None:
            extras = {}
        self.extras = extras
