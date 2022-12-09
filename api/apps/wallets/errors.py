from django.db import IntegrityError


class InsufficientBalance(IntegrityError):
    """
    Raised when a wallet has insufficient balance

    Subclasses :mod:`django.db.IntegrityError` so that it is automatically rolled-back during the transaction lifecycle
    """