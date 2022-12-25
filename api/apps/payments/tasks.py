import json
import logging

from celery import shared_task
from django.db import transaction

from api.apps.payments.models import PaymentRequest
from api.utils.webhook import get_signature_sections, calculate_hmac_signature, compare_signatures

logger = logging.getLogger(__name__)


@shared_task()
def process_webhook_event(stitch_signature_header, request_data):
    payload = json.loads(request_data)
    parsed_payload = json.dumps(payload, separators=(',', ':'))

    if not stitch_signature_header:
        logger.error('Skipping processing of event. X-Stitch-Signature not found in request headers.')

        return

    parsed_signature = get_signature_sections(stitch_signature_header)
    hash_input = f'{parsed_signature["t"]}.{parsed_payload}'
    computed_hash = calculate_hmac_signature(hash_input)
    hashes_match = compare_signatures(computed_hash, parsed_signature['hmac_sha256'])

    if hashes_match:
        stitch_ref = payload['data']['client']['paymentInitiations']['node']['id']
        final_status = payload['data']['client']['paymentInitiations']['node']['status']['__typename']

        try:
            payment_request = PaymentRequest.objects.get(stitch_ref=stitch_ref)
        except PaymentRequest.DoesNotExist:
            logger.error(f'Received unknown payment request {stitch_ref} with status {final_status}')

            return

        status_lookup = {
            'PaymentInitiationCompleted': payment_request.completed(),
            'PaymentInitiationFailed': payment_request.failed(),
            'PaymentInitiationExpired': payment_request.expired(),
        }

        if final_status in status_lookup.keys():
            with transaction.atomic():
                status_lookup.get(payment_request)()
        else:
            logger.error(f'Received unknown payment status {final_status}')

        logger.info(f'Deposit of {payment_request.amount} to user\'s wallet completed successfully.')
    else:
        logger.error('Skipping processing of event. Signature mismatch between X-Stitch-Signature and calculated '
                     'signature')
