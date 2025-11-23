from django.shortcuts import get_object_or_404
from rest_framework import serializers
from events.models import Event
from .models import Ticket

from django.core.cache import cache
from loguru import logger


class TicketSerializer(serializers.ModelSerializer):
    sales_start = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    sales_end = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    event_id = serializers.UUIDField(write_only=True)
    event = serializers.SerializerMethodField(read_only=True)
    CACHE_KEY_DETAIL = "ticket_detail_{}"

    class Meta:
        model = Ticket
        fields = [
            "id",
            "event_id",
            "event",
            "name",
            "price",
            "sales_start",
            "sales_end",
            "quota",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_event(self, obj):
        return obj.event.name

    def validate(self, attrs):
        event_id = attrs.get("event_id")
        sales_start = attrs.get("sales_start")
        sales_end = attrs.get("sales_end")
        quota = attrs.get("quota")
        logger.info(f"Validating Ticket: event_id={event_id}, quota={quota}")

        try:
            if sales_start >= sales_end:
                logger.warning(f"Ticket validation failed: sales_start {sales_start} >= sales_end {sales_end}")
                raise serializers.ValidationError("Sales start must be before sales end.")
            if quota < 1:
                logger.warning(f"Ticket validation failed: quota {quota} is less than 1")
                raise serializers.ValidationError("Quota must be at least 1.")
            get_object_or_404(Event, pk=event_id)
            logger.info(f"Ticket validation successful: event_id={event_id}")
            return attrs
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating Ticket: {e}", exc_info=True)
            raise

    def create(self, validated_data):
        event_id = validated_data.get("event_id")
        ticket_name = validated_data.get("name")
        logger.info(f"Creating Ticket: event_id={event_id}, name={ticket_name}")
        try:
            ticket = Ticket.objects.create(**validated_data)
            logger.info(f"Ticket created successfully: {ticket.id}, name={ticket_name}")
            return ticket
        except Exception as e:
            logger.error(f"Error creating Ticket: {e}", exc_info=True)
            raise

    def update(self, instance, validated_data):
        ticket_id = instance.id
        logger.info(f"Updating Ticket: {ticket_id}")
        try:
            if "event_id" in validated_data:
                get_object_or_404(Event, pk=validated_data["event_id"])
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            cache_key = self.CACHE_KEY_DETAIL.format(instance.id)
            cache.delete(cache_key)
            logger.info(f"Ticket updated successfully: {ticket_id}, cache invalidated")
            return instance
        except Exception as e:
            logger.error(f"Error updating Ticket {ticket_id}: {e}", exc_info=True)
            raise
