from rest_framework import serializers
from django.shortcuts import get_object_or_404
from tickets.models import Ticket
from accounts.models import User
from .models import Registration
from django.utils import timezone


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
        return {
            "username": obj.user.username,
            "email": obj.user.email,
        }

    def get_ticket(self, obj):
        return obj.ticket.name

    def create(self, validated_data):
        return Registration.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if "ticket_id" in validated_data:
            get_object_or_404(Ticket, pk=validated_data["ticket_id"])
        if "user_id" in validated_data:
            get_object_or_404(User, pk=validated_data["user_id"])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
