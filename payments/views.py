from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Payment
from .serializers import PaymentSerializer
from common.permissions import UserPermission
from loguru import logger


class PaymentsPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "payments": data,
            }
        )


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.select_related("registration").all().order_by("-created_at")
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, UserPermission]
    pagination_class = PaymentsPagination

    def list(self, request, *args, **kwargs):
        logger.info(f"Payment list requested by user: {request.user.username}")
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"Payment list retrieved successfully. Count: {response.data.get('count', 0)}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving payment list: {e}", exc_info=True)
            raise

    def retrieve(self, request, *args, **kwargs):
        payment_id = kwargs.get('pk')
        logger.info(f"Payment retrieve requested by user: {request.user.username}, payment_id: {payment_id}")
        try:
            response = super().retrieve(request, *args, **kwargs)
            logger.info(f"Payment retrieved successfully: {payment_id}")
            return response
        except Exception as e:
            logger.error(f"Error retrieving payment {payment_id}: {e}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        registration_id = request.data.get('registration_id')
        amount = request.data.get('amount_paid')
        payment_method = request.data.get('payment_method')
        logger.info(f"Payment create requested by user: {request.user.username}, registration_id: {registration_id}, amount: {amount}, method: {payment_method}")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Payment created successfully: {response.data.get('id')}, registration_id: {registration_id}, amount: {amount}")
            return response
        except Exception as e:
            logger.error(f"Error creating payment for registration {registration_id}: {e}", exc_info=True)
            raise

    def update(self, request, *args, **kwargs):
        payment_id = kwargs.get('pk')
        logger.info(f"Payment update requested by user: {request.user.username}, payment_id: {payment_id}")
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Payment updated successfully: {payment_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating payment {payment_id}: {e}", exc_info=True)
            raise

    def destroy(self, request, *args, **kwargs):
        payment_id = kwargs.get('pk')
        logger.info(f"Payment delete requested by user: {request.user.username}, payment_id: {payment_id}")
        try:
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"Payment deleted successfully: {payment_id}")
            return response
        except Exception as e:
            logger.error(f"Error deleting payment {payment_id}: {e}", exc_info=True)
            raise
