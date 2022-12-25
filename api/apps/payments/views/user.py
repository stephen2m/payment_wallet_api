import json

from django.core import serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from api.apps.payments.models import BankAccount
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
