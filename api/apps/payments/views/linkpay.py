import urllib.parse
import uuid

import requests
import structlog
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView

from api.apps.payments.models import BankAccount, BankAccountToken
from api.apps.payments.serializers.linkpay import PaymentAuthorizationSerializer, FetchUserTokenSerializer, \
    UnlinkAccountSerializer
from api.apps.users.models import User
from api.utils.libs.stitch.errors import LinkPayError
from api.utils.libs.stitch.helpers import generate_code_verifier_challenge_pair
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

            client_response = payment_authorization['clientPaymentAuthorizationRequestCreate']['authorizationRequestUrl']
            scopes = urllib.parse.quote('openid transactions accounts balances accountholders offline_access paymentinitiationrequest')
            client_id = settings.STITCH_CLIENT_ID
            redirect_uri = settings.LINKPAY_REDIRECT_URI
            code_verifier, code_challenge = generate_code_verifier_challenge_pair()
            nonce, state = uuid.uuid4(), uuid.uuid4()

            session_data = {
                'code_verifier': code_verifier
            }

            cache.set(state, session_data, 1800)

            response = {
                'url': f'{client_response}?client_id={client_id}&scope={scopes}&response_type=code&redirect_uri={redirect_uri}'
                       f'&nonce={nonce}&state={state}&code_challenge={code_challenge}&code_challenge_method=S256'
            }
            return Response(
                data=response,
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

            url = 'https://secure.stitch.money/connect/token'
            previous_state = cache.get(state)
            code_verifier = previous_state['code_verifier']

            raw_data = {
                'grant_type': 'authorization_code',
                'client_id': f'{settings.STITCH_CLIENT_ID}',
                'client_secret': f'{settings.STITCH_CLIENT_SECRET}',
                'code': authorization_code,
                'redirect_uri': f'{settings.LINKPAY_REDIRECT_URI}',
                'code_verifier': code_verifier,
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'
            }
            payload = urllib.parse.urlencode(raw_data)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            logger.debug('attempting to fetch user token using authorization code')

            try:
                response = requests.request(
                    'POST', url, headers=headers, data=payload
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                error = f'could not obtain user token: {str(e)}'
                logger.error(error)

                return Response(
                    data={'error': error},
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )

            user_token = response.json()

            try:
                linked_user = request.user
                account_details = fetch_linked_account_details(user_token['access_token'])

                if (linked_user.get_full_name() == account_details['accountHolder']['fullName']) and \
                        linked_user.identification_number == account_details['accountHolder']['identifyingDocument']['number']:
                    existing_linked_accounts = BankAccount.objects.filter(user_id=linked_user.id) \
                        .values_list('account_id', flat=True)

                    if account_details.get('id') in existing_linked_accounts:
                        return Response(
                            data={'success': 'Account already linked for user'},
                            content_type='application/json'
                        )

                    save_linked_account_details(request.user, account_details, user_token)

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

            request_body = {
                'client_id': settings.STITCH_CLIENT_ID,
                'client_secret': settings.STITCH_CLIENT_SECRET,
                'token': refresh_token,
                'token_type_hint': 'refresh_token',
            }

            url = 'https://secure.stitch.money/connect/revocation'
            payload = urllib.parse.urlencode(request_body)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            try:
                response = requests.request(
                    'POST', url, headers=headers, data=payload
                )
                response.raise_for_status()
                logger.info('Refresh token revoked successfully on Stitch')
            except requests.exceptions.RequestException as e:
                logger.error(f'could not revoke refresh token on Stitch: {str(e)}')

            linked_account.delete()
            logger.info('Account records and token successfully deleted')

            return Response(
                data={'success': 'Account successfully unlinked'},
                content_type='application/json'
            )
