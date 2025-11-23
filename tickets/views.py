from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Ticket
from .serializers import TicketSerializer
from common.permissions import IsSuperUserOrAdminOrOrganizer
from django.core.cache import cache
from loguru import logger


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

    def list(self, request, *args, **kwargs):
        logger.info(f"Ticket list requested by user: {request.user.username}")
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"Ticket list retrieved successfully. Count: {response.data.get('count', 0)}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving ticket list: {e}", exc_info=True)
            raise

    def retrieve(self, request, *args, **kwargs):
        ticket_id = kwargs.get("pk")
        logger.info(f"Ticket retrieve requested by user: {request.user.username}, ticket_id: {ticket_id}")
        try:
            instance = self.get_object()
            cache_key = TicketSerializer.CACHE_KEY_DETAIL.format(instance.id)
            cached_ticket = cache.get(cache_key)
            if cached_ticket:
                serializer = self.get_serializer(cached_ticket)
                response = Response(serializer.data, status=status.HTTP_200_OK)
                response["X-Data-Source"] = "cache"
                logger.info(f"Ticket {ticket_id} retrieved from cache")
                return response
            else:
                serializer = self.get_serializer(instance)
                response = Response(serializer.data, status=status.HTTP_200_OK)
                response["X-Data-Source"] = "database"
                cache.set(cache_key, instance, timeout=3600)
                logger.info(f"Ticket {ticket_id} retrieved from database and cached")
                return response
        except Exception as e:
            logger.error(f"Error retrieving ticket {ticket_id}: {e}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        event_id = request.data.get("event_id")
        ticket_name = request.data.get("name")
        logger.info(
            f"Ticket create requested by user: {request.user.username}, event_id: {event_id}, ticket_name: {ticket_name}"
        )
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Ticket created successfully: {response.data.get('id')}, name: {ticket_name}")
            return response
        except Exception as e:
            logger.error(f"Error creating ticket: {e}", exc_info=True)
            raise

    def update(self, request, *args, **kwargs):
        ticket_id = kwargs.get("pk")
        logger.info(f"Ticket update requested by user: {request.user.username}, ticket_id: {ticket_id}")
        try:
            response = super().update(request, *args, **kwargs)
            cache_key = self.serializer_class.CACHE_KEY_DETAIL.format(ticket_id)
            cache.delete(cache_key)
            logger.info(f"Ticket updated successfully: {ticket_id}, cache invalidated")
            return response
        except Exception as e:
            logger.error(f"Error updating ticket {ticket_id}: {e}", exc_info=True)
            raise

    def destroy(self, request, *args, **kwargs):
        ticket_id = kwargs.get("pk")
        logger.info(f"Ticket delete requested by user: {request.user.username}, ticket_id: {ticket_id}")
        try:
            instance = self.get_object()
            cache_key = TicketSerializer.CACHE_KEY_DETAIL.format(instance.id)
            cache.delete(cache_key)
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"Ticket deleted successfully: {ticket_id}, cache invalidated")
            return response
        except Exception as e:
            logger.error(f"Error deleting ticket {ticket_id}: {e}", exc_info=True)
            raise
