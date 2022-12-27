import json

from django.core import serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from api.apps.payments.models import BankAccount, PaymentRequest
from api.utils.permissions import IsActiveUser


class FetchUserLinkedAccounts(RetrieveAPIView):
    permission_classes = (IsActiveUser, )

    def get(self, request, *args, **kwargs):
        linked_accounts = BankAccount.objects\
            .filter(user=request.user)\
            .values('bank_id', 'name', '_account_id_data', 'account_name', 'account_type', 'account_number', 'created')

        return Response(
            data=list(linked_accounts),
            content_type='application/json'
        )


class FetchUserTransactions(RetrieveAPIView):
    permission_classes = (IsActiveUser, )

    def get(self, request, *args, **kwargs):
        transactions = PaymentRequest.objects \
            .filter(user=request.user) \
            .values('amount', 'amount_currency', 'transaction_ref', 'payer_reference', 'status', 'created', 'modified')

        return Response(
            data=list(transactions),
            content_type='application/json'
        )
