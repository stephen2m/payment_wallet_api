from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.urls import path, re_path, include, reverse_lazy
from django.conf.urls.static import static
from django.views import defaults
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
handler500 = 'api.utils.exceptions.drf.server_error_handler'
handler400 = 'rest_framework.exceptions.bad_request'

urlpatterns = [
    path('auth/', include('api.apps.users.urls', namespace='auth')),
    path('payments/', include('api.apps.payments.urls', namespace='payments')),
    # the 'api-root' from django rest-frameworks default router
    # http://www.django-rest-framework.org/api-guide/routers/#defaultrouter
    re_path(r'^$', RedirectView.as_view(url=reverse_lazy('api-root'), permanent=False)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
