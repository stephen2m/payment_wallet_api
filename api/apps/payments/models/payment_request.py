import uuid

from django.conf import settings
from django.db import models

from model_utils.models import TimeStampedModel

from api.utils.enums import PaymentRequestStatus, enum_choices
from api.utils.mixins.models import MoneyMixin


class PaymentRequest(TimeStampedModel, MoneyMixin, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, db_index=True)
    transaction_ref = models.UUIDField(default=uuid.uuid4, db_index=True, null=False, editable=False, primary_key=True)
    stitch_ref = models.CharField(max_length=100, db_index=True, unique=True)
    payer_reference = models.CharField(max_length=12)
    beneficiary_reference = models.CharField(max_length=20)
    status = models.CharField(
        max_length=15,
        choices=enum_choices(PaymentRequestStatus),
        default=PaymentRequestStatus.NEW.name
    )

    def __repr__(self):
        return f'<PaymentRequest {self.transaction_ref} by {self.user.email}: {self.status}>'
