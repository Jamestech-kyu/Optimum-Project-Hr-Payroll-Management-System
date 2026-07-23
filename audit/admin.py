from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action",
        "module",
        "model_name",
        "object_id",
        "ip_address",
        "created_at",
    )

    list_filter = (
        "action",
        "module",
        "model_name",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__username",
        "description",
        "object_repr",
        "object_id",
        "request_path",
    )

    readonly_fields = (
        "user",
        "action",
        "module",
        "model_name",
        "object_id",
        "object_repr",
        "description",
        "old_values",
        "new_values",
        "metadata",
        "ip_address",
        "user_agent",
        "request_method",
        "request_path",
        "created_at",
    )

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False