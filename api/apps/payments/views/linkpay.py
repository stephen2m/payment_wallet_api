import logging
import urllib.parse
import uuid

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView

from api.apps.payments.serializers.linkpay import PaymentAuthorizationSerializer
from api.utils.libs.stitch.errors import LinkPayError
from api.utils.libs.stitch.helpers import generate_code_verifier_challenge_pair
from api.utils.libs.stitch.linkpay.linkpay import LinkPay
from api.utils.permissions import IsActiveUser

logger = logging.getLogger(__name__)


def validate_and_save_linked_user(user_token, user_id):
    pass


class CreatePaymentAuthorizationView(APIView):
    permission_classes = (IsActiveUser,)

    def post(self, request):
        serialized_data = PaymentAuthorizationSerializer(data=request.data)

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
                    'name': request.data.get('full_name'),
                    'email': request.data.get('email'),
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
            'code_verifier': code_verifier,
            'user_id': request.user.id
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


class HandleRedirect(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        authorization_code = request.GET.get('code')
        state = request.GET.get('state')

        if authorization_code is not None and state is not None:
            url = 'https://secure.stitch.money/connect/token'
            previous_state = cache.get(state)
            code_verifier = previous_state['code_verifier']
            user_id = previous_state['user_id']

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

            logger.info('attempting to fetch user token using authorization code')

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
            validate_and_save_linked_user(user_token, user_id)

            return Response(
                data={'success': f'Account successfully linked'},
                content_type='application/json'
            )

        return Response(
            data={'error': 'No authorization code found in Stitch redirect'},
            status=HTTP_400_BAD_REQUEST,
            content_type='application/json'
        )
