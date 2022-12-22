import logging

from django.db import transaction
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST

from api.apps.payments.models import PaymentRequest, BankAccountToken
from api.apps.payments.serializers.payments import InitiateWalletDepositSerializer
from api.utils.code_generator import generate_code
from api.utils.libs.stitch.base import BaseAPI
from api.utils.libs.stitch.errors import LinkPayError
from api.utils.libs.stitch.linkpay.linkpay import LinkPay
from api.utils.permissions import IsActiveUser

logger = logging.getLogger(__name__)


class InitiateWalletDeposit(CreateAPIView):
    permission_classes = (IsActiveUser, )

    def post(self, request):
        serialized_data = InitiateWalletDepositSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            account_token = BankAccountToken.objects.get(account__user=request.user)
            existing_payer_refs = PaymentRequest.objects.values_list('payer_reference', flat=True)
            existing_ben_refs = PaymentRequest.objects.values_list('beneficiary_reference', flat=True)

            # max for payerReference is 12, so remove 2 xters for the default "PW" prefix
            payer_ref = generate_code(existing=existing_payer_refs, size=10)
            # max for beneficiaryReference is 20, so remove 2 xters for the default "PW" prefix
            beneficiary_ref = generate_code(existing=existing_ben_refs, size=18)

            validated_amount = serialized_data.validated_data['amount']
            payment_request = {
                'input': {
                    'amount': {
                        'quantity': f'{validated_amount.amount}',
                        'currency': f'{validated_amount.currency}'
                    },
                    'payerReference': payer_ref,
                    'beneficiaryReference': beneficiary_ref,
                    'externalReference': beneficiary_ref
                }
            }

            with transaction.atomic():
                try:
                    user_token = BaseAPI().rehydrate_user_credentials(account_token.refresh_token)

                    account_token.token_id = user_token['id_token']
                    account_token.refresh_token = user_token['refresh_token']
                    account_token.save()

                    payment_init = LinkPay(token=user_token['access_token']).initiate_user_payment(payment_request)
                    stitch_ref = payment_init.get('userInitiatePayment', {})\
                        .get('paymentInitiation', {})\
                        .get('id', 'error-getting-ref')

                    PaymentRequest(
                        user=request.user,
                        payer_reference=payer_ref,
                        beneficiary_reference=beneficiary_ref,
                        stitch_ref=stitch_ref,
                        amount=validated_amount
                    ).save()

                    return Response(
                        data={'success': f'Deposit of {validated_amount} initiated successfully'},
                        content_type='application/json'
                    )
                except LinkPayError as e:
                    error_prefix = 'Could not initiate your payment request.  Please try again.'
                    logger.error(f'{error_prefix}: {str(e)}')

                    return Response(
                        data={'error': error_prefix},
                        status=HTTP_400_BAD_REQUEST,
                        content_type='application/json'
                    )
                except Exception as e:
                    error_prefix = 'An unexpected error happened trying to initiate payment request'
                    logger.error(f'{error_prefix}: {str(e)}')

                    return Response(
                        data={'error': error_prefix},
                        status=HTTP_500_INTERNAL_SERVER_ERROR,
                        content_type='application/json'
                    )
