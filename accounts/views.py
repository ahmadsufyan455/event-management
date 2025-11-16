from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import User, Group, AssignRole
from .serializers import UserSerializer, GroupSerializer, AssignRoleSerializer
from common.permissions import IsSuperUser, IsAdminOrSuperUser
from rest_framework.pagination import PageNumberPagination


class UserPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "users": data,
            }
        )


class GroupsPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "groups": data,
            }
        )


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("id")
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]
    pagination_class = GroupsPagination


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    pagination_class = UserPagination

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action == "retrieve" or self.action == "update":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrSuperUser()]


class AssignRoleViewSet(viewsets.ModelViewSet):
    queryset = AssignRole.objects.select_related("user", "group").all().order_by("-created_at")
    serializer_class = AssignRoleSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]
