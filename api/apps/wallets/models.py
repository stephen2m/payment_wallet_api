from django.db import models
from django.conf import settings

from model_utils.models import TimeStampedModel

from api.apps.wallets.errors import InsufficientBalance


class Wallet(TimeStampedModel, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, primary_key=True)
    current_balance = models.BigIntegerField(default=0)

    def deposit(self, amount):
        """
        Deposits to the wallet and creates a new transaction with the deposit amount.
        """
        self.transaction_set.create(
            amount=amount,
            running_balance=self.current_balance + amount
        )
        self.current_balance += amount
        self.save()

    def withdraw(self, amount):
        """
        Withdraws from the wallet and creates a new transaction with the withdrawal amount.

        If the withdrawal amount is greater than the current wallet balance, raises a :mod:`InsufficientBalance` error.
        """
        if amount > self.current_balance:
            raise InsufficientBalance(f'This wallet has insufficient balance to withdraw {amount}.')

        self.transaction_set.create(
            amount=-amount,
            running_balance=self.current_balance - amount
        )
        self.current_balance -= amount
        self.save()

    def transfer(self, wallet, amount):
        """
        Uses `deposit` and `withdraw` internally to transfer the specified amount to another wallet.
        """
        self.withdraw(amount)
        wallet.deposit(amount)


class Transaction(TimeStampedModel, models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT)
    amount = models.BigIntegerField(default=0)
    running_balance = models.BigIntegerField(default=0)
