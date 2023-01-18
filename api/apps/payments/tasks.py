import uuid

import structlog
from celery import shared_task
from django_fsm import TransitionNotAllowed

from api.apps.payments.models import PaymentRequest, Wallet, PaymentRequestEvent
from api.utils.enums import PaymentRequestEventType, StitchLinkPayStatus
from api.utils.webhook import get_signature_sections, calculate_hmac_signature, compare_signatures

log = structlog.get_logger('api_requests')


@shared_task()
def process_webhook_event(stitch_signature_header, payload, hash_input):
    webhook_data = payload['data']['client']['paymentInitiations']['node']
    external_ref = webhook_data['externalReference']
    final_status = webhook_data['status']['__typename']

    logger = log.bind(
        event='webhook_processing', request_id=str(uuid.uuid4()), transaction_ref=external_ref, status=final_status
    )

    parsed_signature = get_signature_sections(stitch_signature_header)
    computed_hash = calculate_hmac_signature(hash_input)
    hashes_match = compare_signatures(computed_hash, parsed_signature['hmac_sha256'])

    if hashes_match:
        try:
            payment_request: PaymentRequest = PaymentRequest.objects.get(transaction_ref=external_ref)
        except PaymentRequest.DoesNotExist:
            logger.error(message='Received unknown payment request')
            return

        try:
            match final_status:
                case StitchLinkPayStatus.COMPLETED.name:
                    payment_request.completed()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.COMPLETED.name
                    )

                    user_wallet: Wallet = Wallet.objects.get(user=payment_request.user)
                    user_wallet.deposit(payment_request.amount.amount)
                case StitchLinkPayStatus.FAILED.name:
                    failure_reason = webhook_data['status']['reason']

                    payment_request.failed()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.FAILED.name,
                        event_description=failure_reason
                    )
                case StitchLinkPayStatus.EXPIRED.name:
                    payment_request.expired()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.EXPIRED.name
                    )
                case default:
                    logger.error(message='Received unknown status for a payment request')
        except TransitionNotAllowed as e:
            logger.error(message=f'Error processing payment request: {e}')

        logger.info(message='Processing deposit to user\'s wallet completed successfully.')
    else:
        logger.error(message='Skipping processing of webhook event. Signature mismatch between X-Stitch-Signature and '
                             'calculated signature')
