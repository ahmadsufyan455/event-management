from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Ticket
from .serializers import TicketSerializer
from common.permissions import IsSuperUserOrAdminOrOrganizer


class TicketsPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "tickets": data,
            }
        )


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("event").all().order_by("-created_at")
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrAdminOrOrganizer]
    pagination_class = TicketsPagination
