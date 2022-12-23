from django.urls import path

from api.apps.payments.views.linkpay import CreatePaymentAuthorizationView, VerifyAndLinkUserAccount
from api.apps.payments.views.payments import InitiateWalletDeposit, ProcessPaymentNotification
from api.apps.payments.views.user import FetchUserLinkedAccounts

app_name = 'payments'

urlpatterns = [
    # custom views
    path('linkpay/authorize', CreatePaymentAuthorizationView.as_view(), name='linkpay_authorize'),
    path('linkpay/account/verify', VerifyAndLinkUserAccount.as_view(), name='linkpay_verify_linked_account'),
    path('accounts/user', FetchUserLinkedAccounts.as_view(), name='linked_user_accounts'),
    path('deposit/initiate', InitiateWalletDeposit.as_view(), name='initiate_deposit'),
    path('linkpay/notify', ProcessPaymentNotification.as_view(), name='process_payment_notification'),
]
