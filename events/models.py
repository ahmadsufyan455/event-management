from django.db import models
import uuid

from rest_framework.fields import MinValueValidator

from accounts.models import User
from common.constants import EVENT_STATUS_CHOICES


class Event(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=50, choices=EVENT_STATUS_CHOICES)
    quota = models.IntegerField(validators=[MinValueValidator(1)])
    category = models.CharField(max_length=50)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "events"


class EventPoster(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="posters")
    image = models.ImageField()

    def __str__(self):
        return f"{self.event.name}"

    class Meta:
        db_table = "event_posters"
