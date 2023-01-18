import enum


def enum_choices(enum):
    return [(e.name, e.value) for e in enum]


class PaymentRequestStatus(enum.Enum):
    NEW = 'new'
    COMPLETE = 'complete'
    CLOSED = 'closed'
    FAILED = 'failed'


class IdentificationType(enum.Enum):
    PASSPORT = 'Passport Number'
    ID = 'Identification Number'


class PaymentRequestEventType(enum.Enum):
    INITIATED = 'Payment Initiated'
    COMPLETED = 'Payment Completed'
    FAILED = 'Payment Failed'
    EXPIRED = 'Payment Expired'
    USER_INTERACTION = 'User Interaction Required'
    CONFIRMED = 'Payment Confirmed'


class StitchLinkPayStatus(enum.Enum):
    COMPLETED = 'PaymentInitiationCompleted'
    FAILED = 'PaymentInitiationFailed'
    EXPIRED = 'PaymentInitiationExpired'
