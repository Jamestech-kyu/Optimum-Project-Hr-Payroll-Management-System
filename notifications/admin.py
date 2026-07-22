from django.contrib import admin

from .models import (
    Notification,
    NotificationBroadcast,
    NotificationPreference,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "recipient",
        "notification_type",
        "priority",
        "channel",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "priority",
        "channel",
        "is_read",
        "is_email_sent",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "recipient__email",
        "recipient__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "read_at",
        "email_sent_at",
    )

    date_hierarchy = "created_at"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "in_app_enabled",
        "email_enabled",
        "updated_at",
    )

    search_fields = (
        "user__email",
        "user__username",
    )

    list_filter = (
        "in_app_enabled",
        "email_enabled",
    )


@admin.register(NotificationBroadcast)
class NotificationBroadcastAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "audience",
        "priority",
        "channel",
        "status",
        "scheduled_at",
        "sent_at",
        "created_by",
    )

    list_filter = (
        "audience",
        "priority",
        "channel",
        "status",
    )

    search_fields = (
        "title",
        "message",
    )

    filter_horizontal = (
        "selected_users",
    )

    readonly_fields = (
        "sent_at",
        "created_at",
        "updated_at",
    )
