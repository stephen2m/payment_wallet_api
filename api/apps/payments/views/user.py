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
        # TODO: likely to be slow for huge records, replace with DRF serializer perhaps
        transactions = PaymentRequest.objects \
            .filter(user=request.user) \
            .prefetch_related('paymentrequestevent_set')

        transaction_list = [
            {
                'amount': f'{transaction.amount}',
                'transaction_ref': transaction.transaction_ref,
                'payer_reference': transaction.payer_reference,
                'status': transaction.status,
                'created': transaction.created,
                'modified': transaction.modified,
                'events': [{
                    'event': event.event_type,
                    'event_description': event.event_description,
                    'created': event.created
                } for event in transaction.paymentrequestevent_set.all()]
            } for transaction in transactions
        ]

        return Response(
            data=transaction_list,
            content_type='application/json'
        )
