from rest_framework import serializers

from api.apps.payments.models.payment_request import PaymentRequest


class PaymentRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField( max_digits=19, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    payer_reference = serializers.CharField(max_length=20)
    beneficiary_name = serializers.CharField(max_length=100)
    beneficiary_account = serializers.CharField(max_length=100)
    beneficiary_reference = serializers.CharField(max_length=20)
    beneficiary_bank_id = serializers.CharField(max_length=20)

    def create(self, validated_data):
        return PaymentRequest.objects.create(**validated_data)
