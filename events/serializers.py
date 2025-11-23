import os
import tempfile
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from accounts.models import User
from .models import Event, EventPoster

from minio import Minio


class EventPosterSerializer(serializers.ModelSerializer):
    event = serializers.UUIDField(write_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EventPoster
        fields = ["id", "event", "image", "image_url"]
        read_only_fields = ["id", "image_url"]
        extra_kwargs = {
            "image": {"write_only": True},
        }

    def validate_image(self, value):
        if value.size > 500 * 1024:
            raise serializers.ValidationError("Image size must be less than 500KB.")

        allowed_mime_types = ["image/jpeg", "image/png", "image/jpg"]
        content_type = getattr(value, "content_type", None)

        if content_type not in allowed_mime_types:
            raise serializers.ValidationError("Image must be a JPEG, PNG, or JPG.")

        return value

    def get_minio_client(self):
        return Minio(
            endpoint=os.getenv("MINIO_ENDPOINT_URL"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False,
        )

    def validate(self, attrs):
        get_object_or_404(Event, pk=attrs["event"])
        return attrs

    def create(self, validated_data):
        event_id = validated_data.pop("event")
        image_file = validated_data.pop("image")
        bucket_name = os.getenv("MINIO_BUCKET_NAME")

        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in image_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            object_name = f"{image_file.name}"
            client = self.get_minio_client()

            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)

            client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=temp_file_path,
                content_type=image_file.content_type,
            )
        except Exception as e:
            raise serializers.ValidationError(f"Failed to upload image to MinIO: {e}")
        finally:
            os.remove(temp_file_path)

        return EventPoster.objects.create(
            event_id=event_id,
            image=object_name,
            **validated_data,
        )


class EventSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    organizer_id = serializers.UUIDField(write_only=True)
    organizer = serializers.SerializerMethodField(read_only=True)
    CACHE_KEY_DETAIL = "event_detail_{}"

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
        cache_key = self.CACHE_KEY_DETAIL.format(instance.id)
        cache.delete(cache_key)
        return instance
