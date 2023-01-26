import asyncio
import uuid
from pathlib import Path
from typing import Dict, Union, Any

import structlog
from gql import Client
from gql.transport.exceptions import TransportQueryError
from gql.transport.requests import RequestsHTTPTransport
from graphql import ExecutionResult

from api.utils.libs.stitch.base import BaseAPI, GRAPHQL_ENDPOINT
from api.utils.libs.stitch.errors import LinkPayError

log = structlog.get_logger('graphql_requests')


class LinkPay(BaseAPI):
    def __init__(self, token=None):
        super().__init__()

        if token is None:
            token = self.get_client_token('client_paymentauthorizationrequest')

        transport = RequestsHTTPTransport(
            url=GRAPHQL_ENDPOINT,
            headers={'Authorization': f'Bearer {token}'},
            retries=3
        )

        self.client = Client(transport=transport)

    def create_payment_authorization(self, payment_request: Dict) -> Union[Dict[str, Any], ExecutionResult]:
        logger = log.bind(event='create_payment_authorization', request_id=str(uuid.uuid4()))
        query_path = Path(__file__).parent.joinpath('graphql/payment_authorization.graphql')
        graphql_query = self.load_qraphql_query(query_path)

        try:
            response = self.client.execute(graphql_query, variable_values=payment_request)
            logger.debug(message='Payment authorization created successfully')
            return response
        except TransportQueryError as err:
            logger.error(message=err.errors[0]['message'])
            raise LinkPayError(err.errors[0]['message'])
        except asyncio.exceptions.TimeoutError as err:
            logger.error(message=err)

            raise err

    def get_linked_account_identity(self) -> Union[Dict[str, Any], ExecutionResult]:
        logger = log.bind(event='get_account_details', request_id=str(uuid.uuid4()))
        query_path = Path(__file__).parent.joinpath('graphql/get_account_info.graphql')
        graphql_query = self.load_qraphql_query(query_path)

        try:
            response = self.client.execute(graphql_query)
            logger.debug(message='Linked account details successfully retrieved')
            return response
        except TransportQueryError as err:
            logger.info(message=err.errors[0]['message'])
            raise LinkPayError(err.errors[0]['message'])
        except asyncio.exceptions.TimeoutError as err:
            logger.error(message=err)

            raise err

    def initiate_user_payment(self, payment_request: Dict) -> Union[Dict[str, Any], ExecutionResult]:
        logger = log.bind(event='initiate_payment', request_id=str(uuid.uuid4()))
        query_path = Path(__file__).parent.joinpath('graphql/initiate_payment.graphql')
        graphql_query = self.load_qraphql_query(query_path)

        try:
            response = self.client.execute(graphql_query, variable_values=payment_request)
            logger.debug(message='Payment initiated successfully')
            return response
        except TransportQueryError as err:
            error_detail = err.errors[0]['message']
            error_code = err.errors[0].get('extensions', {}).get('code')
            logger.info(message=err.errors[0]['message'])

            raise LinkPayError(detail=error_detail, code=error_code, extras=err.errors[0].get('extensions', {}))
        except asyncio.exceptions.TimeoutError as err:
            logger.error(message=err)

            raise err
