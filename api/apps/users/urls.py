from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import UserLoginView, UserCreateView, UserListView, UserDetailsUpdateView

app_name = 'auth'

urlpatterns = [
    # custom views
    path('signup', UserCreateView.as_view(), name='signup'),
    path('signin', UserLoginView.as_view(), name='signin'),
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('users', UserListView.as_view(), name='list-users'),
    path('users/<str:id>', UserDetailsUpdateView.as_view(), name='view-update-user'),
]
