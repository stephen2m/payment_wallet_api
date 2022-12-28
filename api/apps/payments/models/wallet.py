from decimal import Decimal

from django.db import models, transaction
from django.conf import settings
from djmoney.models.fields import MoneyField
from djmoney.models.validators import MinMoneyValidator
from djmoney.money import Money

from model_utils.models import TimeStampedModel

from api.apps.payments.errors import InsufficientBalance
from api.utils.mixins.models import MoneyMixin


class Wallet(TimeStampedModel, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, primary_key=True)
    amount = MoneyField(max_digits=19, decimal_places=2, default_currency='ZAR', default=0)

    def deposit(self, amount: Decimal):
        """
        Deposits to the wallet and creates a new transaction with the deposit amount.
        """
        if amount <= 0:
            raise InsufficientBalance('Deposit amount should be greater that 0')

        with transaction.atomic():
            self.transaction_set.create(
                amount=amount,
                running_balance=self.amount.amount + amount
            )
            self.amount.amount += amount
            self.save()

    def withdraw(self, amount: Money):
        """
        Withdraws from the wallet and creates a new transaction with the withdrawal amount.

        If the withdrawal amount is greater than the current wallet balance, raises a :mod:`InsufficientBalance` error.
        """
        if amount > self.amount:
            raise InsufficientBalance(f'This wallet has insufficient balance to withdraw {amount}.')

        with transaction.atomic():
            self.transaction_set.create(
                amount=-amount,
                running_balance=self.amount.amount - amount
            )
            self.amount.amount -= amount
            self.save()

    def transfer(self, wallet, amount: Decimal):
        """
        Uses `deposit` and `withdraw` internally to transfer the specified amount to another wallet.
        """
        self.withdraw(amount)
        wallet.deposit(amount)


class Transaction(TimeStampedModel, MoneyMixin, models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT)
    running_balance = MoneyField(
        max_digits=19, decimal_places=2,
        default_currency='ZAR', validators=[MinMoneyValidator(1)]
    )
