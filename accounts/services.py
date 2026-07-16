from accounts.models import (
    GroupPermission,
    RolePermission,
    RolePermissionGroup,
)


def user_has_permission(user, permission_codename):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if not user.role:
        return False

    direct_permission_exists = RolePermission.objects.filter(
        role=user.role,
        permission__codename=permission_codename,
    ).exists()

    if direct_permission_exists:
        return True

    group_ids = RolePermissionGroup.objects.filter(
        role=user.role,
        group__is_active=True,
    ).values_list(
        "group_id",
        flat=True,
    )

    return GroupPermission.objects.filter(
        group_id__in=group_ids,
        permission__codename=permission_codename,
    ).exists()