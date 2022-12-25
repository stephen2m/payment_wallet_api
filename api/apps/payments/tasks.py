import json
import logging

from celery import shared_task
from django.db import transaction
from django_fsm import TransitionNotAllowed

from api.apps.payments.models import PaymentRequest
from api.utils.webhook import get_signature_sections, calculate_hmac_signature, compare_signatures

logger = logging.getLogger(__name__)


@shared_task()
def process_webhook_event(stitch_signature_header, request_data):
    parsed_payload = json.dumps(request_data, separators=(',', ':'))

    if not stitch_signature_header:
        logger.error('Skipping processing of event. X-Stitch-Signature not found in request headers.')

        return

    parsed_signature = get_signature_sections(stitch_signature_header)
    hash_input = f'{parsed_signature["t"]}.{parsed_payload}'
    computed_hash = calculate_hmac_signature(hash_input)
    hashes_match = compare_signatures(computed_hash, parsed_signature['hmac_sha256'])

    if hashes_match:
        external_ref = request_data['data']['client']['paymentInitiations']['node']['externalReference']
        final_status = request_data['data']['client']['paymentInitiations']['node']['status']['__typename']

        try:
            payment_request = PaymentRequest.objects.get(transaction_ref=external_ref)
        except PaymentRequest.DoesNotExist:
            logger.error(f'Received unknown payment request {external_ref} with status {final_status}')
            return

        try:
            match final_status:
                case 'PaymentInitiationCompleted':
                    payment_request.completed()
                    payment_request.save()
                case 'PaymentInitiationFailed':
                    payment_request.failed()
                    payment_request.save()
                case 'PaymentInitiationExpired':
                    payment_request.expired()
                    payment_request.save()
                case default:
                    logger.error(f'Received unknown payment status {final_status} for ref '
                                 f'{payment_request.transaction_reference} worth {payment_request.amount}')
        except TransitionNotAllowed as e:
            logger.error(f'Error processing payment with ref {payment_request.transaction_reference} worth '
                         f'{payment_request.amount}: {e}')

        logger.info(f'Deposit of {payment_request.amount} to user\'s wallet completed successfully.')
    else:
        logger.error('Skipping processing of event. Signature mismatch between X-Stitch-Signature and calculated '
                     'signature')
