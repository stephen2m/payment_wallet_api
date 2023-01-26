from typing import Literal, Dict
from urllib.parse import urlencode, quote
import uuid

import requests
import structlog
from django.conf import settings
from django.core.cache import cache

from api.utils.libs.stitch.base import BaseAPI
from api.utils.libs.stitch.helpers import generate_code_verifier_challenge_pair

log = structlog.get_logger('api_requests')


class Authentication(BaseAPI):

    def get_user_token(self, authorization_code: str, state: str) -> Dict[str, str]:
        logger = log.bind(event='fetch_user_token', request_id=str(uuid.uuid4()))

        previous_state = cache.get(state)
        code_verifier = previous_state['code_verifier']

        raw_data = {
            'grant_type': 'authorization_code',
            'client_id': f'{self.client_id}',
            'client_secret': f'{self.client_secret}',
            'code': authorization_code,
            'redirect_uri': f'{settings.LINKPAY_REDIRECT_URI}',
            'code_verifier': code_verifier,
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'
        }
        payload = urlencode(raw_data)

        logger.debug('attempting to fetch user token using authorization code')

        try:
            response = requests.request(
                'POST', self.token_endpoint, headers=self.default_headers, data=payload
            )
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            error = f'could not obtain user token: {str(e)}'
            logger.error(error)

            return {
                'error': f'{e}'
            }

    def generate_authorization_url(self, base_url: str, scopes: str) -> dict:
        scopes = quote(scopes)
        client_id = self.client_id
        redirect_uri = self.linkpay_redirect_uri

        code_verifier, code_challenge = generate_code_verifier_challenge_pair()
        nonce, state = uuid.uuid4(), uuid.uuid4()

        session_data = {
            'code_verifier': code_verifier
        }

        cache.set(state, session_data, 1800)

        return {
            'url': f'{base_url}?client_id={client_id}&scope={scopes}&response_type=code&redirect_uri={redirect_uri}'
                   f'&nonce={nonce}&state={state}&code_challenge={code_challenge}&code_challenge_method=S256'
        }

    def revoke_token(self, token: str, token_type: Literal['refresh_token', 'access_token']) -> bool:
        logger = log.bind(event='revoke_token', request_id=str(uuid.uuid4()))

        request_body = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'token': token,
            'token_type_hint': token_type,
        }

        payload = urlencode(request_body)

        try:
            response = requests.request(
                'POST', self.token_revoke_endpoint, headers=self.default_headers, data=payload
            )
            response.raise_for_status()

            return True
        except requests.exceptions.RequestException as e:
            logger.error(f'Could not revoke refresh token on Stitch: {str(e)}')

            return False
