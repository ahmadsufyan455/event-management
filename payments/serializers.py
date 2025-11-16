from rest_framework import serializers
from .models import Payment
from common.constants import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES


class PaymentSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(choices=PAYMENT_METHOD_CHOICES)
    payment_status = serializers.ChoiceField(choices=PAYMENT_STATUS_CHOICES)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    registration_id = serializers.UUIDField(write_only=True)
    registration = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "registration_id",
            "registration",
            "payment_method",
            "payment_status",
            "amount_paid",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_registration(self, obj):
        return str(obj.registration_id)

    def validate(self, attrs):
        if attrs["payment_method"] not in [choice[0] for choice in PAYMENT_METHOD_CHOICES]:
            raise serializers.ValidationError("Invalid payment method.")
        if attrs["payment_status"] not in [choice[0] for choice in PAYMENT_STATUS_CHOICES]:
            raise serializers.ValidationError("Invalid payment status.")
        return attrs

    def create(self, validated_data):
        return Payment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if "payment_method" in validated_data:
            if validated_data["payment_method"] not in [choice[0] for choice in PAYMENT_METHOD_CHOICES]:
                raise serializers.ValidationError("Invalid payment method.")
        if "payment_status" in validated_data:
            if validated_data["payment_status"] not in [choice[0] for choice in PAYMENT_STATUS_CHOICES]:
                raise serializers.ValidationError("Invalid payment status.")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
