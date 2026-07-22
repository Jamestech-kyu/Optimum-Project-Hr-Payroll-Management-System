from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Notification,
    NotificationBroadcast,
    NotificationPreference,
)
from .serializers import (
    NotificationBroadcastSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)
from .services import (
    mark_all_notifications_as_read,
    mark_notification_as_read,
    recent_notifications,
    send_broadcast,
    unread_notification_count,
)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        )

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = self.get_object()

        mark_notification_as_read(notification)

        return Response(
            {"message": "Notification marked as read."}
        )

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        count = mark_all_notifications_as_read(
            request.user
        )

        return Response(
            {
                "message": f"{count} notifications marked as read."
            }
        )

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        return Response(
            {
                "unread": unread_notification_count(
                    request.user
                )
            }
        )

    @action(detail=False, methods=["get"])
    def recent(self, request):
        serializer = NotificationSerializer(
            recent_notifications(request.user),
            many=True,
        )

        return Response(serializer.data)


class NotificationPreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        preference, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )

        serializer = NotificationPreferenceSerializer(
            preference
        )

        return Response(serializer.data)

    def put(self, request):
        preference, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )

        serializer = NotificationPreferenceSerializer(
            preference,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class NotificationBroadcastViewSet(viewsets.ModelViewSet):
    queryset = NotificationBroadcast.objects.all()

    serializer_class = NotificationBroadcastSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user
        )

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        broadcast = self.get_object()

        recipients = send_broadcast(
            broadcast
        )

        return Response(
            {
                "message": (
                    f"Broadcast sent to {recipients} users."
                )
            }
        )
