from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import EventPosterViewSet, EventViewSet

router = DefaultRouter()
router.register(r"events", EventViewSet, basename="event")
urlpatterns = [
    path("events/upload/", EventPosterViewSet.as_view({"post": "create"}), name="event-poster-upload"),
    path("", include(router.urls)),
]
