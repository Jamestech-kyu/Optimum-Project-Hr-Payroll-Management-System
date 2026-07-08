from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    ApprovalStep,
    ApprovalWorkflow,
    CustomUser,
    GroupPermission,
    Permission,
    PermissionGroup,
    Role,
    RolePermission,
    RolePermissionGroup,
    UserDelegation,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)


@admin.action(description="Approve selected users")
def approve_users(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        "module",
        "codename",
        "name",
    )

    search_fields = (
        "codename",
        "name",
        "module",
    )

    list_filter = (
        "module",
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = (
        "role",
        "permission",
    )

    search_fields = (
        "role__name",
        "permission__codename",
    )

    list_filter = (
        "role",
        "permission__module",
    )


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name",)


@admin.register(GroupPermission)
class GroupPermissionAdmin(admin.ModelAdmin):
    list_display = ("group", "permission")
    list_filter = ("group", "permission__module")


@admin.register(RolePermissionGroup)
class RolePermissionGroupAdmin(admin.ModelAdmin):
    list_display = ("role", "group")
    list_filter = ("role", "group")


@admin.register(UserDelegation)
class UserDelegationAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ("name", "module", "is_active")
    list_filter = ("module", "is_active")


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ("workflow", "step_order", "role", "permission_required")
    list_filter = ("workflow", "role")


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