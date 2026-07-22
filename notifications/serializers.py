from rest_framework import serializers

from .models import (
    Notification,
    NotificationBroadcast,
    NotificationPreference,
)


class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "read_at",
            "email_sent_at",
            "is_email_sent",
        )

    def get_sender_name(self, obj):
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.email
        return None


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = "__all__"
        read_only_fields = (
            "user",
            "created_at",
            "updated_at",
        )


class NotificationBroadcastSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationBroadcast
        fields = "__all__"
        read_only_fields = (
            "status",
            "sent_at",
            "created_at",
            "updated_at",
            "created_by",
        )
