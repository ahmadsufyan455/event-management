from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer
from common.permissions import IsSuperUserOrAdminOrOrganizer


class EventsPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "events": data,
            }
        )


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by("-created_at")
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrAdminOrOrganizer]
    pagination_class = EventsPagination
