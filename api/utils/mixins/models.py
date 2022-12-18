from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.models.validators import MinMoneyValidator


class UserMixin(models.Model):
    """
    An abstract base class model that adds user information on creation and update
    """

    created_by = models.ForeignKey(
        'users.User', editable=False, blank=True, null=True,
        on_delete=models.PROTECT, related_name='created_by_%(class)ss'
    )
    updated_by = models.ForeignKey(
        'users.User', editable=False, blank=True, null=True,
        on_delete=models.PROTECT, related_name='updated_by_%(class)ss')

    class Meta:
        abstract = True


class MoneyMixin(models.Model):
    # Banker's rounding
    # https://stackoverflow.com/a/224866/499855
    # https://stackoverflow.com/a/6562018/499855
    amount = MoneyField(max_digits=19, decimal_places=2, default_currency='ZAR', validators=[MinMoneyValidator(1)])

    class Meta:
        abstract = True
