from django.db import models
from registrations.models import Registration
import uuid
from common.constants import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES


class Payment(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="payments")
    payment_method = models.CharField(max_length=255, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=255, choices=PAYMENT_STATUS_CHOICES)
    amount_paid = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration.user.username} - {self.registration.ticket.name}"

    class Meta:
        db_table = "payments"
