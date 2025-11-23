from rest_framework import serializers
from django.shortcuts import get_object_or_404
from tickets.models import Ticket
from accounts.models import User
from .models import Registration
from django.utils import timezone
from loguru import logger


class RegistrationSerializer(serializers.ModelSerializer):
    registered_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    ticket_id = serializers.UUIDField(write_only=True)
    ticket = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Registration
        fields = ["id", "user_id", "user", "ticket_id", "ticket", "registered_at"]
        read_only_fields = ["id", "user", "ticket"]

    def get_user(self, obj):
        return obj.user.username

    def get_ticket(self, obj):
        return obj.ticket.name

    def create(self, validated_data):
        user_id = validated_data.get("user_id")
        ticket_id = validated_data.get("ticket_id")
        logger.info(f"Creating Registration: user_id={user_id}, ticket_id={ticket_id}")
        try:
            registration = Registration.objects.create(**validated_data)
            logger.info(f"Registration created successfully: {registration.id}")
            return registration
        except Exception as e:
            logger.error(f"Error creating Registration: {e}", exc_info=True)
            raise

    def update(self, instance, validated_data):
        registration_id = instance.id
        logger.info(f"Updating Registration: {registration_id}")
        try:
            if "ticket_id" in validated_data:
                get_object_or_404(Ticket, pk=validated_data["ticket_id"])
            if "user_id" in validated_data:
                get_object_or_404(User, pk=validated_data["user_id"])
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            logger.info(f"Registration updated successfully: {registration_id}")
            return instance
        except Exception as e:
            logger.error(f"Error updating Registration {registration_id}: {e}", exc_info=True)
            raise
