from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination, Response
from rest_framework.permissions import IsAuthenticated

from .models import Registration
from .serializers import RegistrationSerializer
from common.permissions import UserPermission

from .task import send_ticket_email
from loguru import logger


class RegistrationsPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "registrations": data,
            }
        )


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.select_related("user", "ticket").all().order_by("-registered_at")
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated, UserPermission]
    pagination_class = RegistrationsPagination

    def list(self, request, *args, **kwargs):
        logger.info(f"Registration list requested by user: {request.user.username}")
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"Registration list retrieved successfully. Count: {response.data.get('count', 0)}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving registration list: {e}", exc_info=True)
            raise

    def retrieve(self, request, *args, **kwargs):
        registration_id = kwargs.get("pk")
        logger.info(
            f"Registration retrieve requested by user: {request.user.username}, registration_id: {registration_id}"
        )
        try:
            response = super().retrieve(request, *args, **kwargs)
            logger.info(f"Registration retrieved successfully: {registration_id}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving registration {registration_id}: {e}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        ticket_id = request.data.get("ticket_id")
        logger.info(
            f"Registration create requested by user: {request.user.username}, user_id: {user_id}, ticket_id: {ticket_id}"
        )
        try:
            response = super().create(request, *args, **kwargs)
            registration_id = response.data.get("id")
            username = response.data.get("user")

            registration = Registration.objects.select_related("user").get(id=registration_id)
            user_email = registration.user.email

            logger.info(f"Registration created successfully: {registration_id}, sending email to {user_email}")
            send_ticket_email.delay(user_email, username, registration_id)
            logger.info(f"Email task queued for registration {registration_id}")
            return response
        except Exception as e:
            logger.error(f"Error creating registration: {e}", exc_info=True)
            raise

    def update(self, request, *args, **kwargs):
        registration_id = kwargs.get("pk")
        logger.info(
            f"Registration update requested by user: {request.user.username}, registration_id: {registration_id}"
        )
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Registration updated successfully: {registration_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating registration {registration_id}: {e}", exc_info=True)
            raise

    def destroy(self, request, *args, **kwargs):
        registration_id = kwargs.get("pk")
        logger.info(
            f"Registration delete requested by user: {request.user.username}, registration_id: {registration_id}"
        )
        try:
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"Registration deleted successfully: {registration_id}")
            return response
        except Exception as e:
            logger.error(f"Error deleting registration {registration_id}: {e}", exc_info=True)
            raise
