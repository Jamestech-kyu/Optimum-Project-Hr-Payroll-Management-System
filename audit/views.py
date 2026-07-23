from rest_framework import permissions
from rest_framework import viewsets

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    queryset = AuditLog.objects.select_related(
        "user"
    ).order_by("-created_at")