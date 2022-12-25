from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers


class InitiateWalletDepositSerializer(serializers.Serializer):
    amount = MoneyField(max_digits=19, decimal_places=2, default_currency="ZAR")
    account_id = serializers.CharField(max_length=50)
