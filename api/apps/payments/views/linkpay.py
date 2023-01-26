import uuid

import structlog
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView

from api.apps.payments.models import BankAccount, BankAccountToken
from api.apps.payments.serializers.linkpay import PaymentAuthorizationSerializer, FetchUserTokenSerializer, \
    UnlinkAccountSerializer
from api.apps.users.models import User
from api.utils.libs.stitch.authentication import Authentication
from api.utils.libs.stitch.errors import LinkPayError
from api.utils.libs.stitch.linkpay.linkpay import LinkPay
from api.utils.permissions import IsActiveUser

log = structlog.get_logger('api_requests')


def fetch_linked_account_details(access_token: str) -> dict:
    logger = log.bind(event='get_account_details', request_id=str(uuid.uuid4()))

    try:
        account_details = LinkPay(token=access_token).get_linked_account_identity()

        return account_details['user']['paymentAuthorization']['bankAccount']
    except LinkPayError as e:
        logger.error(f'could not fetch linked account identity: {str(e)}')

        return {}
    except Exception as e:
        logger.error(f'an unexpected error happened trying to fetch linked account identity: {str(e)}')

        return {}


def save_linked_account_details(user: User, account_details: dict, user_token: dict) -> str:
    account_holder = account_details['accountHolder']

    account = BankAccount.objects.create(
        user_id=user.id,
        bank_id=account_details['bankId'],
        account_id=account_details['id'],
        name=account_details['name'],
        account_name=account_holder['fullName'],
        account_type=account_details['accountType'],
        account_number=account_details['accountNumber'],
    )
    BankAccountToken.objects.create(
        account=account,
        token_id=user_token['id_token'],
        refresh_token=user_token['refresh_token']
    )

    return account.account_id


class CreatePaymentAuthorizationView(APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request):
        serialized_data = PaymentAuthorizationSerializer(data=request.data)
        logger = log.bind(event='payment_authorization', request_id=str(uuid.uuid4()))

        if serialized_data.is_valid(raise_exception=True):
            payment_authorization = {
                'input': {
                    'beneficiary': {
                        'bankAccount': {
                            'name': settings.STITCH_BENEFICIARY_ACCOUNT['name'],
                            'bankId': settings.STITCH_BENEFICIARY_ACCOUNT['bankId'],
                            'accountNumber': settings.STITCH_BENEFICIARY_ACCOUNT['accountNumber'],
                            'accountType': settings.STITCH_BENEFICIARY_ACCOUNT['accountType'],
                            'beneficiaryType': settings.STITCH_BENEFICIARY_ACCOUNT['beneficiaryType'],
                            'reference': 'TestBeneficiaryRef'
                        }
                    },
                    'payer': {
                        'name': serialized_data.validated_data['full_name'],
                        'email': serialized_data.validated_data['email'],
                        'reference': 'TestPayerRef'
                    }
                }
            }

            logger.debug(f'Initiated payment authorization with payload {payment_authorization}')

            try:
                payment_authorization = LinkPay().create_payment_authorization(payment_authorization)
            except LinkPayError as e:
                error = f'could not create payment authorization: {str(e)}'
                logger.error(error)

                return Response(data={'error': error}, status=HTTP_400_BAD_REQUEST, content_type='application/json')
            except Exception as e:
                error = f'an unexpected error happened trying to create payment authorization: {str(e)}'
                logger.error(error)

                return Response(
                    data={'error': error},
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )

            authorization_url = Authentication().generate_authorization_url(
                base_url=payment_authorization['clientPaymentAuthorizationRequestCreate']['authorizationRequestUrl'],
                scopes='openid transactions accounts balances accountholders offline_access paymentinitiationrequest'
            )

            return Response(
                data=authorization_url,
                content_type='application/json'
            )


class VerifyAndLinkUserAccount(APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request):
        serialized_data = FetchUserTokenSerializer(data=request.data)
        logger = log.bind(event='finalize_linking', request_id=str(uuid.uuid4()))

        if serialized_data.is_valid(raise_exception=True):
            authorization_code = serialized_data.validated_data['code']
            state = serialized_data.validated_data['state']

            user_token_response = Authentication().get_user_token(
                state=state, authorization_code=authorization_code
            )

            if 'error' in user_token_response:
                return Response(
                    data=user_token_response,
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )

            try:
                linked_user = request.user
                account_details = fetch_linked_account_details(user_token_response['access_token'])

                if (linked_user.get_full_name() == account_details['accountHolder']['fullName']) and \
                        linked_user.identification_number == account_details['accountHolder']['identifyingDocument']['number']:
                    existing_linked_accounts = BankAccount.objects.filter(user_id=linked_user.id) \
                        .values_list('account_id', flat=True)

                    if account_details.get('id') in existing_linked_accounts:
                        return Response(
                            data={'success': 'Account already linked for user'},
                            content_type='application/json'
                        )

                    save_linked_account_details(request.user, account_details, user_token_response)

                    return Response(
                        data={'success': 'Account successfully linked'},
                        content_type='application/json'
                    )

                return Response(
                    data={'error': 'Mismatch between linked account KYC details and user\'s KYC details'},
                    status=HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )
            except Exception as e:
                logger.error(e)

                return Response(
                    data={'error': f'{e}'},
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )


class UnlinkUserAccount(APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request):
        serialized_data = UnlinkAccountSerializer(data=request.data)
        logger = log.bind(event='unlink_account', request_id=str(uuid.uuid4()), email=request.user.email)

        if serialized_data.is_valid(raise_exception=True):
            try:
                linked_account: BankAccount = BankAccount.objects.get(
                    account_id=serialized_data.validated_data['account_id'],
                    user_id=request.user.id
                )
            except BankAccount.DoesNotExist:
                logger.error(message='Could not find the specified account.')
                return Response(
                    data={'error': 'Please ensure the specified account has been linked.'},
                    status=HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            try:
                refresh_token = linked_account.bankaccounttoken.refresh_token
            except ObjectDoesNotExist:
                logger.error(message='Specified account does not have a refresh token saved.')
                return Response(
                    data={'error': 'Please ensure the specified account has been linked.'},
                    status=HTTP_400_BAD_REQUEST,
                    content_type='application/json'
                )

            token_revoked = Authentication().revoke_token(
                token=refresh_token, token_type='refresh_token'
            )

            if token_revoked:
                logger.info('Refresh token revoked successfully on Stitch')
                linked_account.delete()
                logger.info('Account records and token successfully deleted')

                return Response(
                    data={'success': 'Account successfully unlinked'},
                    content_type='application/json'
                )

            return Response(
                data={'error': 'Account not unlinked'},
                status=HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )
