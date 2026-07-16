from accounts.models import (
    RolePermission,
    RolePermissionGroup,
    GroupPermission,
    UserDelegation,
)


def user_has_permission(user, permission_codename):
    """
    Check whether a user has a permission either directly
    or through a permission group.
    """

    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if not user.role:
        return False

    # Direct Role Permission
    if RolePermission.objects.filter(
        role=user.role,
        permission__codename=permission_codename,
    ).exists():
        return True

    # Permission inherited from groups
    groups = RolePermissionGroup.objects.filter(
        role=user.role
    ).values_list("group", flat=True)

    return GroupPermission.objects.filter(
        group_id__in=groups,
        permission__codename=permission_codename,
    ).exists()


def get_permission_scope(user, permission_codename):
    """
    Return the assigned data scope for a permission.
    """

    role_permission = RolePermission.objects.filter(
        role=user.role,
        permission__codename=permission_codename,
    ).first()

    if role_permission:
        return role_permission.data_scope

    return None