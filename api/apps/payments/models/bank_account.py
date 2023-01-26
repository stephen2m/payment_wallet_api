import os

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from encrypted_fields import fields
from model_utils.models import TimeStampedModel, UUIDModel


def default_token_expiry():
    return timezone.now() + timezone.timedelta(days=365)


def get_hash_key():
    return os.getenv('FIELD_ENCRYPTION_KEY')


class BankAccount(TimeStampedModel, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    bank_id = models.CharField(max_length=30)
    _account_id_data = fields.EncryptedCharField(max_length=50, default='')
    account_id = fields.SearchField(hash_key=get_hash_key, encrypted_field_name='_account_id_data')
    name = models.CharField(max_length=100)
    account_name = fields.EncryptedCharField(max_length=100)
    account_type = models.CharField(max_length=100)
    account_number = fields.EncryptedCharField(max_length=100)


class BankAccountToken(TimeStampedModel, UUIDModel, models.Model):
    account = models.OneToOneField(BankAccount, on_delete=models.CASCADE)
    token_id = models.TextField()
    refresh_token = fields.EncryptedCharField(max_length=100)
    refresh_token_expiry = models.DateTimeField(default=default_token_expiry)


@receiver(post_delete, sender=BankAccount)
def auto_delete_account_with_token(sender, instance, **kwargs):
    instance.bankaccounttoken.delete()
