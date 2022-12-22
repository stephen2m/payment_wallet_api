from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone

from encrypted_fields import fields
from model_utils.models import TimeStampedModel, UUIDModel


class BankAccount(TimeStampedModel, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    bank_id = models.CharField(max_length=30)
    account_id = fields.EncryptedCharField(max_length=100)
    name = models.CharField(max_length=100)
    account_name = fields.EncryptedCharField(max_length=100)
    account_type = models.CharField(max_length=100)
    account_number = fields.EncryptedCharField(max_length=100)


class BankAccountToken(TimeStampedModel, UUIDModel, models.Model):
    account = models.OneToOneField(BankAccount, on_delete=models.PROTECT)
    token_id = models.TextField()
    refresh_token = fields.EncryptedCharField(max_length=100)
    refresh_token_expiry = models.DateTimeField()
