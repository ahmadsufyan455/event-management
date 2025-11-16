from rest_framework.permissions import BasePermission


def _is_admin(user):
    return user.is_authenticated and user.roles.filter(group__name__iexact="admin").exists()


def _is_event_organizer(user):
    return user.is_authenticated and user.roles.filter(group__name__iexact="organizer").exists()


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsAdminOrSuperUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or _is_admin(user)))


class IsSuperUserOrAdminOrOrganizer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if request.method == "GET":
            return bool(user and user.is_authenticated)
        return bool(
            user and user.is_authenticated and (user.is_superuser or _is_admin(user) or _is_event_organizer(user))
        )

    def has_object_permission(self, request, view, obj):
        if (
            request.user.is_authenticated
            and _is_event_organizer(request.user)
            and (request.method == "PUT" or request.method == "PATCH" or request.method == "DELETE")
        ):
            if obj.organizer_id != request.user.id:
                return False
        return super().has_object_permission(request, view, obj)


class UserPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if request.method == "GET":
            if view.action == "list":
                return bool(user and user.is_authenticated and (user.is_superuser or _is_admin(user)))
            if view.action == "retrieve":
                return bool(user and user.is_authenticated)
        return bool(user and user.is_authenticated and (user.is_superuser or _is_admin(user)))
