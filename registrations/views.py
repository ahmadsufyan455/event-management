from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Registration
from .serializers import RegistrationSerializer
from common.permissions import RegistrationPermission

# Create your views here.


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.select_related("user", "ticket").all().order_by("-registered_at")
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated, RegistrationPermission]
