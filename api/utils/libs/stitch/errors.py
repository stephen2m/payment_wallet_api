class InstantPayError(Exception):
    pass


class PaymentRequestStatusError(Exception):
    pass


class StitchConfigurationIncomplete(Exception):
    pass


class StitchClientAuthenticationError(Exception):
    pass


class BankAccountVerificationError(Exception):
    pass


class LinkPayError(Exception):
    pass
