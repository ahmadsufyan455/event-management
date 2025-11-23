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
from loguru import logger
from rest_framework.exceptions import NotFound


def get_minio_client():
    try:
        client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT_URL"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False,
        )
        logger.info("MinIO client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Error initializing MinIO client: {e}", exc_info=True)
        raise


class EventsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "events": data,
            }
        )

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)

        try:
            page_number = int(page_number)
            if page_number < 1:
                page_number = 1
        except (TypeError, ValueError):
            page_number = 1

        try:
            self.page = paginator.page(page_number)
        except Exception:
            if paginator.num_pages > 0:
                self.page = paginator.page(paginator.num_pages)
            else:
                self.page = paginator.page(1)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related("organizer").all().order_by("-created_at")
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrAdminOrOrganizer]
    pagination_class = EventsPagination

    def list(self, request, *args, **kwargs):
        logger.info(f"Event list requested by user: {request.user.username}")
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"Event list retrieved successfully. Count: {response.data.get('count', 0)}")
            return response
        except NotFound as e:
            # Handle invalid page number
            logger.warning(f"Invalid page requested: {request.query_params.get('page', 'not provided')}")
            # Return first page instead of error
            request.query_params._mutable = True
            request.query_params["page"] = "1"
            request.query_params._mutable = False
            response = super().list(request, *args, **kwargs)
            logger.info(
                f"Event list retrieved successfully (corrected to page 1). Count: {response.data.get('count', 0)}"
            )
            return response
        except Exception as e:
            logger.error(f"Error retrieving event list: {e}", exc_info=True)
            raise

    def retrieve(self, request, *args, **kwargs):
        event_id = kwargs.get("pk")
        logger.info(f"Event retrieve requested by user: {request.user.username}, event_id: {event_id}")
        try:
            instance = self.get_object()
            cache_key = EventSerializer.CACHE_KEY_DETAIL.format(instance.id)

            cached_event = cache.get(cache_key)

            if cached_event:
                serializer = self.get_serializer(cached_event)
                response = Response(serializer.data, status=status.HTTP_200_OK)
                response["X-Data-Source"] = "cache"
                logger.info(f"Event {event_id} retrieved from cache")
                return response
            else:
                serializer = self.get_serializer(instance)
                response = Response(serializer.data, status=status.HTTP_200_OK)
                response["X-Data-Source"] = "database"
                cache.set(cache_key, instance, timeout=3600)
                logger.info(f"Event {event_id} retrieved from database and cached")
                return response
        except Exception as e:
            logger.error(f"Error retrieving event {event_id}: {e}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        logger.info(f"Event create requested by user: {request.user.username}, event_name: {request.data.get('name')}")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Event created successfully: {response.data.get('id')}, name: {response.data.get('name')}")
            return response
        except Exception as e:
            logger.error(f"Error creating event: {e}", exc_info=True)
            raise

    def update(self, request, *args, **kwargs):
        event_id = kwargs.get("pk")
        logger.info(f"Event update requested by user: {request.user.username}, event_id: {event_id}")
        try:
            response = super().update(request, *args, **kwargs)
            cache_key = self.serializer_class.CACHE_KEY_DETAIL.format(event_id)
            cache.delete(cache_key)
            logger.info(f"Event updated successfully: {event_id}, cache invalidated")
            return response
        except Exception as e:
            logger.error(f"Error updating event {event_id}: {e}", exc_info=True)
            raise

    def destroy(self, request, *args, **kwargs):
        event_id = kwargs.get("pk")
        logger.info(f"Event delete requested by user: {request.user.username}, event_id: {event_id}")
        try:
            instance = self.get_object()
            cache_key = self.serializer_class.CACHE_KEY_DETAIL.format(instance.id)
            cache.delete(cache_key)
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"Event deleted successfully: {event_id}, cache invalidated")
            return response
        except Exception as e:
            logger.error(f"Error deleting event {event_id}: {e}", exc_info=True)
            raise

    @action(detail=True, methods=["get"], url_path="poster")
    def poster(self, request, pk=None):
        logger.info(f"Event poster requested by user: {request.user.username}, event_id: {pk}")
        try:
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

            logger.info(f"Event posters retrieved successfully for event {pk}, count: {len(serialized_posters)}")
            return Response(serialized_posters, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving event posters for event {pk}: {e}", exc_info=True)
            raise


class EventPosterViewSet(viewsets.ModelViewSet):
    queryset = EventPoster.objects.all()
    serializer_class = EventPosterSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrAdminOrOrganizer]
    parser_classes = [MultiPartParser, FormParser]

    def list(self, request, *args, **kwargs):
        logger.info(f"EventPoster list requested by user: {request.user.username}")
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(
                f"EventPoster list retrieved successfully. Count: {len(response.data) if isinstance(response.data, list) else response.data.get('count', 0)}"
            )
            return response
        except Exception as e:
            logger.error(f"Error retrieving EventPoster list: {e}", exc_info=True)
            raise

    def retrieve(self, request, *args, **kwargs):
        poster_id = kwargs.get("pk")
        logger.info(f"EventPoster retrieve requested by user: {request.user.username}, poster_id: {poster_id}")
        try:
            response = super().retrieve(request, *args, **kwargs)
            logger.info(f"EventPoster retrieved successfully: {poster_id}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving EventPoster {poster_id}: {e}", exc_info=True)
            raise

    # def create(self, request, *args, **kwargs):
    #     event_id = request.data.get("event")
    #     logger.info(f"EventPoster create requested by user: {request.user.username}, event_id: {event_id}")
    #     try:
    #         serializer = self.get_serializer(data=request.data)
    #         serializer.is_valid(raise_exception=True)
    #         instance = serializer.save()
    #         logger.info(f"EventPoster created successfully: {instance.id}, event_id: {event_id}")
    #         return Response({"messages": "upload image success"}, status=status.HTTP_201_CREATED)
    #     except Exception as e:
    #         logger.error(f"Error creating EventPoster for event {event_id}: {e}", exc_info=True)
    #         raise

    def destroy(self, request, *args, **kwargs):
        poster_id = kwargs.get("pk")
        logger.info(f"EventPoster delete requested by user: {request.user.username}, poster_id: {poster_id}")
        try:
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"EventPoster deleted successfully: {poster_id}")
            return response
        except Exception as e:
            logger.error(f"Error deleting EventPoster {poster_id}: {e}", exc_info=True)
            raise
