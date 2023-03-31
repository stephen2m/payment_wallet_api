import logging
import os
from random import randrange

import requests
from django.conf import settings
from django.core.cache import cache
from gql import gql
from graphql import DocumentNode

from api.utils.libs.stitch.errors import StitchConfigurationIncomplete

GRAPHQL_ENDPOINT = os.environ.get('STITCH_API_ENDPOINT', 'https://api.stitch.money/graphql')
CLIENT_TOKEN_ENDPOINT = os.environ.get('STITCH_CLIENT_TOKEN_ENDPOINT', 'https://secure.stitch.money/connect/token')
REVOKE_TOKEN_ENDPOINT = os.environ.get('STITCH_TOKEN_REVOKE_ENDPOINT', 'https://secure.stitch.money/connect/revocation')
STITCH_CLIENT_ID = settings.STITCH_CLIENT_ID
STITCH_CLIENT_SECRET = settings.STITCH_CLIENT_SECRET
LINKPAY_REDIRECT_URI = settings.LINKPAY_REDIRECT_URI
LINKPAY_USER_INTERACTION_URI = settings.LINKPAY_USER_INTERACTION_URI

logger = logging.getLogger(__name__)


class BaseAPI(object):
    """
    Base class for the Stitch API wrapper
    """
    def __init__(self):
        errors = []
        if STITCH_CLIENT_ID is None:
            errors.append({
                'client_id': 'Please specify your Stitch client ID in the environment variable STITCH_CLIENT_ID'
            })

        if STITCH_CLIENT_SECRET is None:
            errors.append({
                'client_secret': 'Please specify your Stitch client secret in the environment variable STITCH_CLIENT_SECRET'
            })

        if LINKPAY_REDIRECT_URI is None:
            errors.append({
                'redirect_uri': 'Please specify the redirect URI to use during linking in the environment variable LINKPAY_REDIRECT_URI'
            })

        if LINKPAY_USER_INTERACTION_URI is None:
            errors.append({
                'user_interaction_redirect': 'Please specify the redirect URI to use during linking in the environment variable LINKPAY_USER_INTERACTION_URI'
            })

        if errors:
            raise StitchConfigurationIncomplete(errors)

        self.client_id = STITCH_CLIENT_ID
        self.client_secret = STITCH_CLIENT_SECRET
        self.token_endpoint = CLIENT_TOKEN_ENDPOINT
        self.token_revoke_endpoint = REVOKE_TOKEN_ENDPOINT
        self.linkpay_redirect_uri = LINKPAY_REDIRECT_URI
        self.default_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def load_qraphql_query(self, path: str) -> DocumentNode:
        with open(path) as f:
            return gql(f.read())

    def get_client_token(self, scope: str) -> str:
        cache_key = f'{self.client_id}_access_token'
        access_token = cache.get(cache_key)

        if access_token:
            logger.debug('access token reused')
            return access_token

        payload = {
            'client_id': self.client_id,
            'audience': self.token_endpoint,
            'scope': scope,
            'grant_type': 'client_credentials',
            'client_secret': self.client_secret
        }

        try:
            response = requests.post(self.token_endpoint, data=payload, headers=self.default_headers)
            response.raise_for_status()
            logger.debug(f'Client token with scope {scope} obtained successfully')
        except requests.exceptions.RequestException as err:
            logger.error(f'Error getting client token {err}')
            raise StitchClientAuthenticationError(err)

        access_token = response.json()['access_token']
        # the token will expire in 3600 seconds, so set a random time to expire it in the cache
        expiry_sec = randrange(150) + 3300
        cache.set(cache_key, access_token, expiry_sec)
        logger.debug('access token saved to cache for reuse')

        return access_token

    def refresh_user_credentials(self, refresh_token: str) -> dict:
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': f'{refresh_token}'
        }

        try:
            response = requests.post(self.token_endpoint, data=payload, headers=self.default_headers)
            response.raise_for_status()
            logger.debug('User token refreshed')
        except requests.exceptions.RequestException as err:
            logger.error(f'Error refreshing user credentials {err}')
            raise SystemExit(err)

        return response.json()
