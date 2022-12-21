from django.urls import path

from api.apps.payments.views.linkpay import CreatePaymentAuthorizationView, VerifyAndLinkUserAccount

app_name = 'payments'

urlpatterns = [
    # custom views
    path('linkpay/authorize', CreatePaymentAuthorizationView.as_view(), name='linkpay_authorize'),
    path('linkpay/account/verify', VerifyAndLinkUserAccount.as_view(), name='linkpay_verify_linked_account'),
]
