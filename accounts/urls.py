from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, UserViewSet, AssignRoleViewSet

router = DefaultRouter()
router.register(r"groups", GroupViewSet, basename="group")
router.register(r"users", UserViewSet, basename="user")
router.register(r"assign-roles", AssignRoleViewSet, basename="assignrole")

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
