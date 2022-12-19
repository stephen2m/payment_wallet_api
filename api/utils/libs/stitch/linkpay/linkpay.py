import asyncio
import logging
import os.path
from pathlib import Path
from typing import Dict, Union, Any

from gql import Client
from gql.transport.exceptions import TransportQueryError
from gql.transport.requests import RequestsHTTPTransport
from graphql import ExecutionResult

from api.utils.libs.stitch.base import BaseAPI, GRAPHQL_ENDPOINT
from api.utils.libs.stitch.errors import LinkPayError

logger = logging.getLogger(__name__)


class LinkPay(BaseAPI):
    def __init__(self, token=None):
        super().__init__()

        if token is None:
            client_token = self.generate_client_token('client_paymentauthorizationrequest')
            headers = {'Authorization': f'Bearer {client_token}'}
        else:
            headers = {'Authorization': f'Bearer {token}'}
        transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT, headers=headers, retries=3)

        self.client = Client(transport=transport)

    def create_payment_authorization(self, payment_request: Dict) -> Union[Dict[str, Any], ExecutionResult]:
        query_path = Path(__file__).parent.joinpath('graphql/payment_authorization.graphql')
        graphql_query = self.load_qraphql_query(query_path)

        try:
            response = self.client.execute(graphql_query, variable_values=payment_request)
            logger.debug(f'Payment authorization created successfully')
            return response
        except TransportQueryError as err:
            logger.error(err.errors[0]['message'])
            raise LinkPayError(err.errors[0]['message'])
        except asyncio.exceptions.TimeoutError as err:
            logger.error(err)

            raise err

    def get_linked_account_identity(self) -> Union[Dict[str, Any], ExecutionResult]:
        query_path = Path(__file__).parent.joinpath('graphql/get_account_info.graphql')
        graphql_query = self.load_qraphql_query(query_path)

        try:
            response = self.client.execute(graphql_query)
            logger.debug(f'Linked account details successfully retrieved')
            return response
        except TransportQueryError as err:
            logger.error(err.errors[0]['message'])
            raise LinkPayError(err.errors[0]['message'])
        except asyncio.exceptions.TimeoutError as err:
            logger.error(err)

            raise err



