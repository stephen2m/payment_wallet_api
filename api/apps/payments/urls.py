from django.urls import path

from api.apps.payments.views.linkpay import CreatePaymentAuthorizationView, HandleRedirect

app_name = 'payments'

urlpatterns = [
    # custom views
    path('linkpay/authorize', CreatePaymentAuthorizationView.as_view(), name='linkpay_authorize'),
    path('linkpay/return', HandleRedirect.as_view(), name='linkpay_redirect'),
]
