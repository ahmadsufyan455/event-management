from django.shortcuts import get_object_or_404
from rest_framework import serializers
from events.models import Event
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    sales_start = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    sales_end = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    event_id = serializers.UUIDField(write_only=True)
    event = serializers.SerializerMethodField(read_only=True)

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
        if attrs["sales_start"] >= attrs["sales_end"]:
            raise serializers.ValidationError("Sales start must be before sales end.")
        if attrs["quota"] < 1:
            raise serializers.ValidationError("Quota must be at least 1.")
        get_object_or_404(Event, pk=attrs["event_id"])
        return attrs

    def create(self, validated_data):
        return Ticket.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if "event_id" in validated_data:
            get_object_or_404(Event, pk=validated_data["event_id"])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
