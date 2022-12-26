from django.db import transaction
from rest_framework import serializers

from .models import User
from ..payments.models.wallet import Wallet


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'short_name', 'last_login')
        read_only_fields = ('email', 'last_login')


class CreateUserSerializer(serializers.ModelSerializer[User]):

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        user = User.objects.create_user(**validated_data)
        Wallet.objects.create(user=user)

        return user

    class Meta:
        model = User
        fields = ('email', 'full_name', 'short_name', 'password', 'identification_type', 'identification_number')
        extra_kwargs = {'password': {'write_only': True}}


class UserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100, required=False, allow_blank=True, allow_null=True)
    full_name = serializers.CharField(max_length=255)
    short_name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True)

    def update(self, *args, **kwargs):
        user = args[0]
        user.full_name = self.validated_data['full_name']
        user.email = self.validated_data['email']
        user.short_name = self.validated_data['short_name']
        user.save()

        return user
