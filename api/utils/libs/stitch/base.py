import logging
import os

import requests
from django.conf import settings
from django.core.cache import cache
from gql import gql
from graphql import DocumentNode

from api.utils.libs.stitch.errors import StitchConfigurationIncomplete

GRAPHQL_ENDPOINT = os.environ.get('STITCH_API_ENDPOINT', 'https://api.stitch.money/graphql')
CLIENT_TOKEN_ENDPOINT = os.environ.get('STITCH_CLIENT_TOKEN_ENDPOINT', 'https://secure.stitch.money/connect/token')
REVOKE_TOKEN_ENDPOINT = os.environ.get('STITCH_TOKEN_REVOKE_ENDPOINT', 'https://secure.stitch.money/connect/revocation')

logger = logging.getLogger(__name__)


class BaseAPI(object):
    """
    Base class for the Stitch API wrapper
    """
    def __init__(self):
        if settings.STITCH_CLIENT_ID is None:
            raise StitchConfigurationIncomplete('Please specify your Stitch client ID in the environment variable STITCH_CLIENT_ID')

        if settings.STITCH_CLIENT_SECRET is None:
            raise StitchConfigurationIncomplete('Please specify your Stitch client secret in the environment variable STITCH_CLIENT_SECRET')

        self.client_id = settings.STITCH_CLIENT_ID
        self.client_secret = settings.STITCH_CLIENT_SECRET
        self.token_endpoint = CLIENT_TOKEN_ENDPOINT
        self.token_revoke_endpoint = REVOKE_TOKEN_ENDPOINT
        self.linkpay_redirect_uri = settings.LINKPAY_REDIRECT_URI
        self.default_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def load_qraphql_query(self, path: str) -> DocumentNode:
        with open(path) as f:
            return gql(f.read())

    def get_client_token(self, scope: str) -> str:
        access_token = cache.get('access_token')

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
            raise SystemExit(err)

        access_token = response.json()['access_token']
        # the token will expire in 3600 seconds, so expire it in the cache slightly earlier in 57 minutes
        cache.set('access_token', access_token, 3420)
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
