from rest_framework.exceptions import PermissionDenied

from .scopes import (
    scope_employee_queryset,
    scope_related_employee_queryset,
)


def check_employee_object_permission(
    user,
    employee,
    permission_codename="employees.view",
):
    """
    Verify access to a specific Employee object.
    """

    queryset = scope_employee_queryset(
        user=user,
        queryset=employee.__class__.objects.filter(
            id=employee.id,
        ),
        permission_codename=permission_codename,
    )

    if not queryset.exists():
        raise PermissionDenied(
            "You do not have permission to access this employee."
        )


def check_related_employee_permission(
    user,
    queryset,
    employee_field,
    object_id,
    permission_codename,
):
    """
    Verify access to any model that has an Employee relation.
    """

    scoped_queryset = scope_related_employee_queryset(
        user=user,
        queryset=queryset.filter(id=object_id),
        employee_field=employee_field,
        permission_codename=permission_codename,
    )

    if not scoped_queryset.exists():
        raise PermissionDenied(
            "You do not have permission to access this record."
        )

    return scoped_queryset.first()