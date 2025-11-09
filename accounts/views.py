from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import User, Group, AssignRole
from .serializers import UserSerializer, GroupSerializer, AssignRoleSerializer
from .permissions import IsSuperUser, IsAdminOrSuperUser


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("id")
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]


class AssignRoleViewSet(viewsets.ModelViewSet):
    queryset = AssignRole.objects.select_related("user", "group").all().order_by("-created_at")
    serializer_class = AssignRoleSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]
