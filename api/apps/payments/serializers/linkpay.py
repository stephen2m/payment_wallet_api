from rest_framework import serializers


class PaymentAuthorizationSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)
    full_name = serializers.CharField(max_length=150)


class FetchUserTokenSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
