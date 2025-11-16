from django.db import models
import uuid
from tickets.models import Ticket
from accounts.models import User


class Registration(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registrations")
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ticket.name}"

    class Meta:
        db_table = "registrations"
