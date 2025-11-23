from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import User, Group, AssignRole
from .serializers import UserSerializer, GroupSerializer, AssignRoleSerializer
from common.permissions import IsSuperUser, IsAdminOrSuperUser
from rest_framework.pagination import PageNumberPagination
from loguru import logger


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

    def list(self, request, *args, **kwargs):
        logger.info(f"Group list requested by user: {request.user.username}")
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"Group list retrieved successfully. Count: {response.data.get('count', 0)}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving group list: {e}", exc_info=True)
            raise

    def retrieve(self, request, *args, **kwargs):
        logger.info(f"Group retrieve requested by user: {request.user.username}, group_id: {kwargs.get('pk')}")
        try:
            response = super().retrieve(request, *args, **kwargs)
            logger.info(f"Group retrieved successfully: {kwargs.get('pk')}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving group {kwargs.get('pk')}: {e}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        logger.info(f"Group create requested by user: {request.user.username}, data: {request.data}")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Group created successfully: {response.data.get('id')}")
            return response
        except Exception as e:
            logger.error(f"Error creating group: {e}", exc_info=True)
            raise

    def update(self, request, *args, **kwargs):
        logger.info(f"Group update requested by user: {request.user.username}, group_id: {kwargs.get('pk')}")
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Group updated successfully: {kwargs.get('pk')}")
            return response
        except Exception as e:
            logger.error(f"Error updating group {kwargs.get('pk')}: {e}", exc_info=True)
            raise

    def destroy(self, request, *args, **kwargs):
        logger.info(f"Group delete requested by user: {request.user.username}, group_id: {kwargs.get('pk')}")
        try:
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"Group deleted successfully: {kwargs.get('pk')}")
            return response
        except Exception as e:
            logger.error(f"Error deleting group {kwargs.get('pk')}: {e}", exc_info=True)
            raise


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

    def list(self, request, *args, **kwargs):
        logger.info(
            f"User list requested by user: {request.user.username if request.user.is_authenticated else 'anonymous'}"
        )
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"User list retrieved successfully. Count: {response.data.get('count', 0)}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving user list: {e}", exc_info=True)
            raise

    def retrieve(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        logger.info(f"User retrieve requested by user: {request.user.username}, target_user_id: {user_id}")
        try:
            response = super().retrieve(request, *args, **kwargs)
            logger.info(f"User retrieved successfully: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        logger.info(
            f"User create requested. Username: {request.data.get('username')}, Email: {request.data.get('email')}"
        )
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(
                f"User created successfully: {response.data.get('id')}, Username: {response.data.get('username')}"
            )
            return response
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            raise

    def update(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        logger.info(f"User update requested by user: {request.user.username}, target_user_id: {user_id}")
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"User updated successfully: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
            raise

    def destroy(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        logger.info(f"User delete requested by user: {request.user.username}, target_user_id: {user_id}")
        try:
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"User deleted successfully: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
            raise


class AssignRoleViewSet(viewsets.ModelViewSet):
    queryset = AssignRole.objects.select_related("user", "group").all().order_by("-created_at")
    serializer_class = AssignRoleSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]

    def list(self, request, *args, **kwargs):
        logger.info(f"AssignRole list requested by user: {request.user.username}")
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"AssignRole list retrieved successfully. Count: {response.data.get('count', 0)}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving AssignRole list: {e}", exc_info=True)
            raise

    def retrieve(self, request, *args, **kwargs):
        role_id = kwargs.get("pk")
        logger.info(f"AssignRole retrieve requested by user: {request.user.username}, role_id: {role_id}")
        try:
            response = super().retrieve(request, *args, **kwargs)
            logger.info(f"AssignRole retrieved successfully: {role_id}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving AssignRole {role_id}: {e}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        logger.info(
            f"AssignRole create requested by user: {request.user.username}, user_id: {request.data.get('user_id')}, group_id: {request.data.get('group_id')}"
        )
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"AssignRole created successfully: {response.data.get('id')}")
            return response
        except Exception as e:
            logger.error(f"Error creating AssignRole: {e}", exc_info=True)
            raise

    def destroy(self, request, *args, **kwargs):
        role_id = kwargs.get("pk")
        logger.info(f"AssignRole delete requested by user: {request.user.username}, role_id: {role_id}")
        try:
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"AssignRole deleted successfully: {role_id}")
            return response
        except Exception as e:
            logger.error(f"Error deleting AssignRole {role_id}: {e}", exc_info=True)
            raise
