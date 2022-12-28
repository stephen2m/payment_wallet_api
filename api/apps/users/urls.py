from django.urls import re_path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import UserLoginView, UserCreateView, UserListView, UserDetailsUpdateView

app_name = 'auth'

urlpatterns = [
    # custom views
    re_path(r'signup$', UserCreateView.as_view(), name='signup'),
    re_path(r'signin$', UserLoginView.as_view(), name='signin'),
    re_path(r'refresh$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'users$', UserListView.as_view(), name='list-users'),
    re_path(r'users/me$', UserDetailsUpdateView.as_view(), name='view-update-user'),
]
