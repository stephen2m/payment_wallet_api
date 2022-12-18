from rest_framework import serializers


class PaymentAuthorizationSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)
    full_name = serializers.CharField(max_length=20)
