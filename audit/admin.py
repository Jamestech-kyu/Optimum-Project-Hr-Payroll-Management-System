from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "action",
        "module",
        "object_id",
        "ip_address",
        "created_at",
    )

    search_fields = (
        "user__username",
        "module",
        "description",
        "object_id",
    )

    list_filter = (
        "action",
        "module",
        "created_at",
    )

    readonly_fields = (
        "user",
        "action",
        "module",
        "description",
        "object_id",
        "ip_address",
        "created_at",
    )