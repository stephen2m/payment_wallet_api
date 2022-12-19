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
