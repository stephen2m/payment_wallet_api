import uuid

from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition

from model_utils.models import TimeStampedModel

from api.utils.enums import PaymentRequestStatus, enum_choices
from api.utils.mixins.models import MoneyMixin


class PaymentRequest(TimeStampedModel, MoneyMixin, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, db_index=True)
    transaction_ref = models.UUIDField(default=uuid.uuid4, db_index=True, null=False, editable=False, primary_key=True)
    stitch_ref = models.CharField(max_length=100, null=True, default='')
    payer_reference = models.CharField(max_length=12)
    beneficiary_reference = models.CharField(max_length=20)
    status = FSMField(default=PaymentRequestStatus.NEW.name)

    def __repr__(self):
        return f'<PaymentRequest {self.transaction_ref} by {self.user.email}: {self.status}>'

    def can_finalise(self):
        return self.status == PaymentRequestStatus.NEW.name

    @transition(field=status, source=PaymentRequestStatus.NEW.name, target=PaymentRequestStatus.COMPLETE.name, conditions=[can_finalise])
    def completed(self):
        pass

    @transition(field=status, source=PaymentRequestStatus.NEW.name, target=PaymentRequestStatus.FAILED.name, conditions=[can_finalise])
    def failed(self):
        pass

    @transition(field=status, source=PaymentRequestStatus.NEW.name, target=PaymentRequestStatus.FAILED.name, conditions=[can_finalise])
    def expired(self):
        pass
