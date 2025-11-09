from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Ticket
from .serializers import TicketSerializer
from common.permissions import IsAdminOrSuperUser


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("event").all().order_by("-created_at")
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
