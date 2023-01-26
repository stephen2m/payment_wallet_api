from django.urls import re_path

from api.apps.payments.views.linkpay import CreatePaymentAuthorizationView, VerifyAndLinkUserAccount, UnlinkUserAccount
from api.apps.payments.views.payments import InitiateWalletDeposit, ProcessPaymentNotification
from api.apps.payments.views.user import FetchUserLinkedAccounts, FetchUserTransactions

app_name = 'payments'

urlpatterns = [
    # custom views
    re_path(r'linkpay/authorize$', CreatePaymentAuthorizationView.as_view(), name='linkpay_authorize'),
    re_path(r'linkpay/account/verify$', VerifyAndLinkUserAccount.as_view(), name='linkpay_verify_linked_account'),
    re_path(r'accounts/user/unlink$', UnlinkUserAccount.as_view(), name='unlink_user_account'),
    re_path(r'accounts/user$', FetchUserLinkedAccounts.as_view(), name='linked_user_accounts'),
    re_path(r'deposit/initiate$', InitiateWalletDeposit.as_view(), name='initiate_deposit'),
    re_path(r'linkpay/notify$', ProcessPaymentNotification.as_view(), name='process_linkpay_webhook'),
    re_path(r'transactions/user$', FetchUserTransactions.as_view(), name='user_payment_requests'),
]
