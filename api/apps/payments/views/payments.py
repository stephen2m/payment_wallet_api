import logging
import uuid

from django.conf import settings
from django.db import transaction
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST

from api.apps.payments.models import PaymentRequest, BankAccountToken
from api.apps.payments.serializers.payments import InitiateWalletDepositSerializer
from api.apps.payments.tasks import process_webhook_event
from api.apps.users.models import User
from api.utils.code_generator import generate_code
from api.utils.libs.stitch.base import BaseAPI
from api.utils.libs.stitch.errors import LinkPayError
from api.utils.libs.stitch.linkpay.linkpay import LinkPay
from api.utils.permissions import IsActiveUser

logger = logging.getLogger(__name__)


class ProcessPaymentNotification(CreateAPIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        stitch_signature_header = request.META.get('HTTP_X_STITCH_SIGNATURE', '')

        process_webhook_event.delay(stitch_signature_header, request.data)

        return Response(
            data={'success': 'Webhook received successfully'},
            content_type='application/json'
        )


def create_payment_request(payment_request: dict, stitch_ref: str, user: User) -> PaymentRequest:
    with transaction.atomic():
        return PaymentRequest(
            user=user,
            transaction_ref=payment_request.get('input').get('externalReference'),
            payer_reference=payment_request.get('input').get('payerReference'),
            beneficiary_reference=payment_request.get('input').get('beneficiaryReference'),
            stitch_ref=stitch_ref,
            amount=payment_request.get('input').get('amount').get('quantity'),
            amount_currency=payment_request.get('input').get('amount').get('currency')
        ).save()


class InitiateWalletDeposit(CreateAPIView):
    permission_classes = (IsActiveUser,)

    def post(self, request):
        serialized_data = InitiateWalletDepositSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            account_token = BankAccountToken.objects.get(
                account__account_id=serialized_data.validated_data['account_id']
            )
            existing_payer_refs = PaymentRequest.objects.values_list('payer_reference', flat=True)
            existing_ben_refs = PaymentRequest.objects.values_list('beneficiary_reference', flat=True)

            # max for payerReference is 12, so remove 2 xters for the default "PW" prefix
            payer_ref = generate_code(existing=existing_payer_refs, size=10)
            # max for beneficiaryReference is 20, so remove 2 xters for the default "PW" prefix
            beneficiary_ref = generate_code(existing=existing_ben_refs, size=18)

            validated_amount = serialized_data.validated_data['amount']
            external_reference = uuid.uuid4()
            payment_request = {
                'input': {
                    'amount': {
                        'quantity': f'{validated_amount.amount}',
                        'currency': f'{validated_amount.currency}'
                    },
                    'payerReference': payer_ref,
                    'beneficiaryReference': beneficiary_ref,
                    'externalReference': f'{external_reference}'
                }
            }

            try:
                user_token = BaseAPI().rehydrate_user_credentials(account_token.refresh_token)

                account_token = BankAccountToken.objects.get(account__account_id='YWNjb3VudC9jYXBpdGVjLzQ3MDAxMC8xOTkxMzkzNjY5')

                account_token.token_id = user_token['id_token']
                account_token.refresh_token = user_token['refresh_token']
                account_token.save()

                payment_init = LinkPay(token=user_token['access_token']).initiate_user_payment(payment_request)

                stitch_ref = payment_init.get('userInitiatePayment', {}) \
                    .get('paymentInitiation', {}) \
                    .get('id', 'error-getting-ref')

                create_payment_request(payment_request, stitch_ref, request.user)

                return Response(
                    data={'success': f'Deposit of {validated_amount} initiated successfully'},
                    content_type='application/json'
                )
            except LinkPayError as e:
                error_context = e.extras
                if (e.get_codes()) == 'USER_INTERACTION_REQUIRED':
                    if error_context:
                        logger.info(f'User interaction required for payment')
                        redirect_uri = settings.LINKPAY_USER_INTERACTION_URI
                        user_interaction_uri = error_context.get('userInteractionUrl')
                        response = {
                            'url': f'{user_interaction_uri}?redirect_uri={redirect_uri}'
                        }

                        stitch_ref = error_context.get('id', 'error-getting-ref')
                        create_payment_request(payment_request, stitch_ref, request.user)

                        return Response(
                            data=response,
                            content_type='application/json'
                        )
                    else:
                        logger.error('Could not determine user integration URL from error message context')

                error_prefix = 'Could not initiate your payment request.'
                logger.error(f'{error_prefix}: {str(e)}')

                return Response(
                    data={'error': f'{error_prefix} Please try again.'},
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
