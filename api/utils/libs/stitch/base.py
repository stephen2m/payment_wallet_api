import logging
import os

import requests
from django.conf import settings
from gql import gql
from graphql import DocumentNode

from api.utils.libs.stitch.errors import StitchConfigurationIncomplete

GRAPHQL_ENDPOINT = os.environ.get('STITCH_API_ENDPOINT', 'https://api.stitch.money/graphql')
CLIENT_TOKEN_ENDPOINT = os.environ.get('STITCH_CLIENT_TOKEN_ENDPOINT', 'https://secure.stitch.money/connect/token')
CLIENT_TOKEN_ASSERTION_TYPE = 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'

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

    def load_qraphql_query(self, path: str) -> DocumentNode:
        with open(path) as f:
            return gql(f.read())

    def generate_client_token(self, scope: str) -> str:
        payload = {
            'client_id': self.client_id,
            'audience': CLIENT_TOKEN_ENDPOINT,
            'scope': scope,
            'grant_type': 'client_credentials',
            'client_secret': self.client_secret,
            'client_assertion_type': CLIENT_TOKEN_ASSERTION_TYPE
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(CLIENT_TOKEN_ENDPOINT, data=payload, headers=headers)
            response.raise_for_status()
            logger.debug(f'Client token with scope {scope} obtained successfully')
        except requests.exceptions.RequestException as err:
            logger.error(f'Error making client generate call to {CLIENT_TOKEN_ENDPOINT} {err}')
            raise SystemExit(err)

        return response.json().get('access_token')
