import os
import tempfile
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from accounts.models import User
from .models import Event, EventPoster

from minio import Minio
from loguru import logger


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
        logger.info(f"Validating image: size={value.size}, content_type={getattr(value, 'content_type', None)}")
        if value.size > 500 * 1024:
            logger.warning(f"Image size validation failed: {value.size} bytes exceeds 500KB limit")
            raise serializers.ValidationError("Image size must be less than 500KB.")

        allowed_mime_types = ["image/jpeg", "image/png", "image/jpg"]
        content_type = getattr(value, "content_type", None)

        if content_type not in allowed_mime_types:
            logger.warning(f"Image content type validation failed: {content_type}")
            raise serializers.ValidationError("Image must be a JPEG, PNG, or JPG.")

        logger.info(f"Image validation successful: size={value.size}, content_type={content_type}")
        return value

    def get_minio_client(self):
        return Minio(
            endpoint=os.getenv("MINIO_ENDPOINT_URL"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False,
        )

    def validate(self, attrs):
        event_id = attrs.get("event")
        logger.info(f"Validating EventPoster: event_id={event_id}")
        try:
            get_object_or_404(Event, pk=event_id)
            logger.info(f"EventPoster validation successful: event_id={event_id}")
            return attrs
        except Exception as e:
            logger.error(f"Error validating EventPoster for event {event_id}: {e}", exc_info=True)
            raise

    def create(self, validated_data):
        event_id = validated_data.pop("event")
        image_file = validated_data.pop("image")
        bucket_name = os.getenv("MINIO_BUCKET_NAME")
        object_name = f"{image_file.name}"

        logger.info(f"Creating EventPoster: event_id={event_id}, image_name={object_name}, size={image_file.size}")
        temp_file_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in image_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            logger.info(f"Temporary file created: {temp_file_path}")

            client = self.get_minio_client()

            if not client.bucket_exists(bucket_name):
                logger.info(f"Bucket {bucket_name} does not exist, creating it")
                client.make_bucket(bucket_name)

            logger.info(f"Uploading image to MinIO: bucket={bucket_name}, object={object_name}")
            client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=temp_file_path,
                content_type=image_file.content_type,
            )
            logger.info(f"Image uploaded successfully to MinIO: {object_name}")

            poster = EventPoster.objects.create(
                event_id=event_id,
                image=object_name,
                **validated_data,
            )
            logger.info(f"EventPoster created successfully: {poster.id}, event_id={event_id}")
            return poster
        except Exception as e:
            logger.error(f"Error creating EventPoster for event {event_id}: {e}", exc_info=True)
            raise serializers.ValidationError(f"Failed to upload image to MinIO: {e}")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Temporary file removed: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Error removing temporary file {temp_file_path}: {e}")


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
        quota = attrs.get("quota")
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        organizer_id = attrs.get("organizer_id")
        logger.info(f"Validating Event: quota={quota}, organizer_id={organizer_id}")

        try:
            if quota < 1:
                logger.warning(f"Event validation failed: quota {quota} is less than 1")
                raise serializers.ValidationError("Quota must be at least 1.")
            if start_time >= end_time:
                logger.warning(f"Event validation failed: start_time {start_time} >= end_time {end_time}")
                raise serializers.ValidationError("Start time must be before end time.")
            get_object_or_404(User, pk=organizer_id)
            logger.info(f"Event validation successful: organizer_id={organizer_id}")
            return attrs
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating Event: {e}", exc_info=True)
            raise

    def create(self, validated_data):
        event_name = validated_data.get("name")
        organizer_id = validated_data.get("organizer_id")
        logger.info(f"Creating Event: name={event_name}, organizer_id={organizer_id}")
        try:
            event = Event.objects.create(**validated_data)
            logger.info(f"Event created successfully: {event.id}, name={event_name}")
            return event
        except Exception as e:
            logger.error(f"Error creating Event: {e}", exc_info=True)
            raise

    def update(self, instance, validated_data):
        event_id = instance.id
        logger.info(f"Updating Event: {event_id}")
        try:
            if "organizer_id" in validated_data:
                get_object_or_404(User, pk=validated_data["organizer_id"])
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            cache_key = self.CACHE_KEY_DETAIL.format(instance.id)
            cache.delete(cache_key)
            logger.info(f"Event updated successfully: {event_id}, cache invalidated")
            return instance
        except Exception as e:
            logger.error(f"Error updating Event {event_id}: {e}", exc_info=True)
            raise
