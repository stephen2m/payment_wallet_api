import uuid

import structlog
from celery import shared_task
from django_fsm import TransitionNotAllowed

from api.apps.payments.models import PaymentRequest, Wallet, PaymentRequestEvent
from api.utils.enums import PaymentRequestEventType
from api.utils.webhook import get_signature_sections, calculate_hmac_signature, compare_signatures

log = structlog.get_logger('api_requests')


@shared_task()
def process_webhook_event(stitch_signature_header, payload, hash_input):
    external_ref = payload['data']['client']['paymentInitiations']['node']['externalReference']
    final_status = payload['data']['client']['paymentInitiations']['node']['status']['__typename']

    logger = log.bind(
        event='webhook_processing', request_id=str(uuid.uuid4()), id=external_ref, status=final_status
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
                case 'PaymentInitiationCompleted':
                    payment_request.completed()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.COMPLETED.name
                    )

                    user_wallet: Wallet = Wallet.objects.get(user=payment_request.user)
                    user_wallet.deposit(payment_request.amount.amount)
                case 'PaymentInitiationFailed':
                    failure_reason = payload['data']['client']['paymentInitiations']['node']['status']['reason']

                    payment_request.failed()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.FAILED.name,
                        event_description=failure_reason
                    )
                case 'PaymentInitiationExpired':
                    payment_request.expired()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.EXPIRED.name
                    )
                case default:
                    logger.error(message=f'Received unknown webhook event for a payment worth {payment_request.amount}')
        except TransitionNotAllowed as e:
            logger.error(message=f'Error processing payment worth {payment_request.amount}: {e}')

        logger.info(message=f'Processing deposit of {payment_request.amount} to user\'s wallet completed successfully.')
    else:
        logger.error(message='Skipping processing of event. Signature mismatch between X-Stitch-Signature and '
                             'calculated signature')
