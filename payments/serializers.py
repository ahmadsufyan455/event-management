from rest_framework import serializers
from .models import Payment
from common.constants import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES
from loguru import logger


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
        payment_method = attrs.get("payment_method")
        payment_status = attrs.get("payment_status")
        registration_id = attrs.get("registration_id")
        logger.info(f"Validating Payment: registration_id={registration_id}, method={payment_method}, status={payment_status}")
        
        try:
            if payment_method not in [choice[0] for choice in PAYMENT_METHOD_CHOICES]:
                logger.warning(f"Payment validation failed: invalid payment method {payment_method}")
                raise serializers.ValidationError("Invalid payment method.")
            if payment_status not in [choice[0] for choice in PAYMENT_STATUS_CHOICES]:
                logger.warning(f"Payment validation failed: invalid payment status {payment_status}")
                raise serializers.ValidationError("Invalid payment status.")
            logger.info(f"Payment validation successful: registration_id={registration_id}")
            return attrs
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating Payment: {e}", exc_info=True)
            raise

    def create(self, validated_data):
        registration_id = validated_data.get("registration_id")
        amount = validated_data.get("amount_paid")
        logger.info(f"Creating Payment: registration_id={registration_id}, amount={amount}")
        try:
            payment = Payment.objects.create(**validated_data)
            logger.info(f"Payment created successfully: {payment.id}, registration_id={registration_id}")
            return payment
        except Exception as e:
            logger.error(f"Error creating Payment: {e}", exc_info=True)
            raise

    def update(self, instance, validated_data):
        payment_id = instance.id
        logger.info(f"Updating Payment: {payment_id}")
        try:
            if "payment_method" in validated_data:
                if validated_data["payment_method"] not in [choice[0] for choice in PAYMENT_METHOD_CHOICES]:
                    logger.warning(f"Payment update validation failed: invalid payment method {validated_data['payment_method']}")
                    raise serializers.ValidationError("Invalid payment method.")
            if "payment_status" in validated_data:
                if validated_data["payment_status"] not in [choice[0] for choice in PAYMENT_STATUS_CHOICES]:
                    logger.warning(f"Payment update validation failed: invalid payment status {validated_data['payment_status']}")
                    raise serializers.ValidationError("Invalid payment status.")
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            logger.info(f"Payment updated successfully: {payment_id}")
            return instance
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating Payment {payment_id}: {e}", exc_info=True)
            raise
