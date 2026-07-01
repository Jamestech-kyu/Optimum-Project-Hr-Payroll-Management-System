from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)


@admin.action(description="Approve selected users")
def approve_users(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = (
        "id",
        "email",
        "username",
        "role",
        "is_approved",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    list_display_links = ("id", "email", "username")

    list_filter = (
        "role",
        "is_approved",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = ("email", "username")
    ordering = ("id",)
    actions = [approve_users]

    fieldsets = UserAdmin.fieldsets + (
        (
            "HR Payroll Fields",
            {
                "fields": (
                    "role",
                    "is_approved",
                    "phone_number",
                    "profile_picture",
                    "last_login_ip",
                )
            },
        ),
    )

    readonly_fields = ("last_login_ip", "created_at", "updated_at")