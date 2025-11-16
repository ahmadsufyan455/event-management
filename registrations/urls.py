from rest_framework.routers import DefaultRouter
from .views import RegistrationViewSet
from django.urls import include, path

router = DefaultRouter()
router.register(r"registrations", RegistrationViewSet, basename="registration")

urlpatterns = [
    path("", include(router.urls)),
]
