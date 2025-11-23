from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Ticket
from .serializers import TicketSerializer
from common.permissions import IsSuperUserOrAdminOrOrganizer
from django.core.cache import cache


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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = TicketSerializer.CACHE_KEY_DETAIL.format(instance.id)
        cached_ticket = cache.get(cache_key)
        if cached_ticket:
            serializer = self.get_serializer(cached_ticket)
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response["X-Data-Source"] = "cache"
            return response
        else:
            serializer = self.get_serializer(instance)
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response["X-Data-Source"] = "database"
            cache.set(cache_key, instance, timeout=3600)
            return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = TicketSerializer.CACHE_KEY_DETAIL.format(instance.id)
        cache.delete(cache_key)
        return super().destroy(request, *args, **kwargs)
