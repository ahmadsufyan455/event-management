from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Event
from .serializers import EventSerializer
from common.permissions import IsSuperUserOrAdminOrOrganizer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by("-created_at")
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrAdminOrOrganizer]
