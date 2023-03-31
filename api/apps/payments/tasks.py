import json
import uuid

import structlog
from celery import shared_task
from django.conf import settings
from django_fsm import TransitionNotAllowed
from svix.webhooks import Webhook, WebhookVerificationError

from api.apps.payments.models import PaymentRequest, Wallet, PaymentRequestEvent
from api.utils.enums import PaymentRequestEventType, StitchLinkPayStatus

log = structlog.get_logger('api_requests')


@shared_task()
def process_linkpay_webhook_event(payload, headers):
    webhook_data = payload['data']['client']['paymentInitiations']['node']
    external_ref = webhook_data['externalReference']
    payment_status = webhook_data['status']['__typename']

    logger = log.bind(
        event='webhook_processing', request_id=str(uuid.uuid4()), transaction_ref=external_ref, status=payment_status
    )

    try:
        webhook_secret = settings.LINKPAY_WEBHOOK_SECRET_KEY
        # we need to ensure the data doesn't have any spaces between values
        parsed_payload = json.dumps(payload, separators=(',', ':'))
        wh = Webhook(webhook_secret)
        wh.verify(parsed_payload, headers)

        try:
            payment_request: PaymentRequest = PaymentRequest.objects.get(transaction_ref=external_ref)
        except PaymentRequest.DoesNotExist:
            logger.error(message='Received unknown payment request')
            return

        try:
            match payment_status:
                case StitchLinkPayStatus.COMPLETED.value:
                    payment_request.completed()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.COMPLETED.name
                    )

                    user_wallet: Wallet = Wallet.objects.get(user=payment_request.user)
                    user_wallet.deposit(payment_request.amount.amount)
                case StitchLinkPayStatus.FAILED.value:
                    failure_reason = webhook_data['status']['reason']

                    payment_request.failed()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.FAILED.name,
                        event_description=failure_reason
                    )
                case StitchLinkPayStatus.EXPIRED.value:
                    payment_request.expired()
                    payment_request.save()

                    payment_request.paymentrequestevent_set.create(
                        event_type=PaymentRequestEventType.EXPIRED.name
                    )
                case default:
                    logger.error(message='Received unknown status in payment request')
        except TransitionNotAllowed as e:
            logger.error(message=f'Error processing payment request: {e}')

        logger.info(message='Processed deposit to user\'s wallet successfully.')
    except WebhookVerificationError as e:
        logger.error(message=f'Could not verify webhook: {e}')
        return
