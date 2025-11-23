import os
from minio import Minio
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Event, EventPoster
from rest_framework.decorators import action
from .serializers import EventPosterSerializer, EventSerializer
from common.permissions import IsSuperUserOrAdminOrOrganizer
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.cache import cache


def get_minio_client():
    return Minio(
        endpoint=os.getenv("MINIO_ENDPOINT_URL"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )


class EventsPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "events": data,
            }
        )


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related("organizer").all().order_by("-created_at")
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrAdminOrOrganizer]
    pagination_class = EventsPagination

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = EventSerializer.CACHE_KEY_DETAIL.format(instance.id)

        cached_event = cache.get(cache_key)

        if cached_event:
            serializer = self.get_serializer(cached_event)
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response["X-Data-Source"] = "cache"
            return response
        else:
            serializer = self.get_serializer(instance)
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response["X-Data-Source"] = "database"
            cache.set(cache_key, instance, timeout=3600)
            return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = self.serializer_class.CACHE_KEY_DETAIL.format(instance.id)
        cache.delete(cache_key)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="poster")
    def poster(self, request, pk=None):
        event = self.get_object()
        posters = event.posters.all()

        bucket_name = os.getenv("MINIO_BUCKET_NAME")

        serialized_posters = []
        for poster in posters:
            client = get_minio_client()
            presigned_url = client.presigned_get_object(
                bucket_name,
                poster.image.name,
                response_headers={
                    "response-content-type": "image/jpeg",
                },
            )
            serialized_posters.append({"id": poster.id, "image_url": presigned_url})

        return Response(serialized_posters, status=status.HTTP_200_OK)


class EventPosterViewSet(viewsets.ModelViewSet):
    queryset = EventPoster.objects.all()
    serializer_class = EventPosterSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrAdminOrOrganizer]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"messages": "upload image success"}, status=status.HTTP_201_CREATED)
