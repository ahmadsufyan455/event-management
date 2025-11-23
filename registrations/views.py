from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination, Response
from rest_framework.permissions import IsAuthenticated

from .models import Registration
from .serializers import RegistrationSerializer
from common.permissions import UserPermission

from .task import send_ticket_email


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

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        send_ticket_email.delay(
            response.data["user"]["email"],
            response.data["user"]["username"],
            response.data["id"],
        )
        return response
