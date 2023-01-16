from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.apps.payments.models import Wallet
from api.apps.users.models import User
from api.apps.users.serializers import CreateUserSerializer, UserSerializer, UserUpdateSerializer
from api.utils.permissions import IsActiveAdminUser, IsNotAuthenticated, IsActiveUser


class UserLoginView(APIView):
    permission_classes = (IsNotAuthenticated,)

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)

        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            wallet = Wallet.objects.get(user=user)
            response = {
                'user': user.json(),
                'wallet': {
                    'balance': f'{wallet.amount}',
                    'last_activity': f'{wallet.modified}'
                },
                'tokens': {
                    'refresh': f'{refresh}',
                    'access': f'{refresh.access_token}',
                },
            }

            update_last_login(None, user)
            return Response(data=response, content_type='application/json')

        error = 'Your user account has been deactivated.' if user else 'Invalid Credentials'
        return Response(data={'error': error}, status=HTTP_400_BAD_REQUEST)


class UserCreateView(CreateAPIView):
    model = get_user_model()
    serializer_class = CreateUserSerializer
    permission_classes = (AllowAny,)


class UserListView(ListAPIView):
    permission_classes = (IsActiveAdminUser,)
    serializer_class = UserSerializer

    def get_queryset(self):
        filter_kwargs = {}
        only_active = self.request.query_params.get('onlyActive', 'False')

        if only_active.title() == 'True':
            filter_kwargs['is_active'] = True

        return User.objects.exclude(id=self.request.user.id).filter(**filter_kwargs)


class UserDetailsUpdateView(RetrieveUpdateAPIView):
    permission_classes = (IsActiveUser,)

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        if self.request.method == 'PUT':
            return UserUpdateSerializer

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(self.get_object(), data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            instance = self.get_object()

        return Response(UserSerializer(instance).data, status=HTTP_200_OK)
