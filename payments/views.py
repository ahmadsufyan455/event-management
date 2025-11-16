from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from .models import Payment
from .serializers import PaymentSerializer
from common.permissions import UserPermission


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.select_related("registration").all().order_by("-created_at")
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, UserPermission]
