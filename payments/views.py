from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Payment
from .serializers import PaymentSerializer
from common.permissions import UserPermission


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
