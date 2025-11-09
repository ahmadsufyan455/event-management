from django.db import models
import uuid

from events.models import Event


class Ticket(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    name = models.CharField(max_length=255, blank=False, null=False)
    price = models.IntegerField(blank=False, null=False)
    sales_start = models.DateTimeField(blank=False, null=False)
    sales_end = models.DateTimeField(blank=False, null=False)
    quota = models.IntegerField(blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event.name} - {self.name}"

    class Meta:
        db_table = "tickets"
