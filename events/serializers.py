from django.shortcuts import get_object_or_404
from rest_framework import serializers

from accounts.models import User
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    organizer_id = serializers.UUIDField(write_only=True)
    organizer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "description",
            "location",
            "start_time",
            "end_time",
            "status",
            "quota",
            "category",
            "organizer_id",
            "organizer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "organizer"]

    def get_organizer(self, obj):
        return {
            "id": str(obj.organizer_id),
            "username": obj.organizer.username,
            "email": obj.organizer.email,
        }

    def validate(self, attrs):
        if attrs["quota"] < 1:
            raise serializers.ValidationError("Quota must be at least 1.")
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("Start time must be before end time.")
        get_object_or_404(User, pk=attrs["organizer_id"])
        return attrs

    def create(self, validated_data):
        return Event.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if "organizer_id" in validated_data:
            get_object_or_404(User, pk=validated_data["organizer_id"])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
