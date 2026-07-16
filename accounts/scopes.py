from django.db.models import Q


SCOPE_RANK = {
    "OWN": 1,
    "TEAM": 2,
    "DEPARTMENT": 3,
    "BRANCH": 4,
    "COMPANY": 5,
    "ORGANIZATION": 6,
    "GLOBAL": 7,
}


def get_user_employee(user):
    """
    Return the employee profile linked to the authenticated user.
    """

    if not user or not user.is_authenticated:
        return None

    try:
        return user.employee_profile
    except AttributeError:
        return None


def get_permission_scope(user, permission_codename):
    """
    Resolve the user's highest data scope for a permission.

    Checks:
    1. Direct role permissions
    2. Permissions inherited from permission groups
    """

    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return "GLOBAL"

    if not user.role:
        return None

    scopes = []

    direct_permissions = user.role.role_permissions.filter(
        permission__codename=permission_codename,
    ).values_list(
        "data_scope",
        flat=True,
    )

    scopes.extend(direct_permissions)

    group_permissions = user.role.permission_groups.filter(
        group__permissions__permission__codename=permission_codename,
    ).values_list(
        "group__permissions__permission__role_permissions__data_scope",
        flat=True,
    )

    scopes.extend(
        scope
        for scope in group_permissions
        if scope
    )

    if not scopes:
        return None

    return max(
        scopes,
        key=lambda scope: SCOPE_RANK.get(scope, 0),
    )


def scope_employee_queryset(
    user,
    queryset,
    permission_codename="employees.view",
):
    """
    Restrict an Employee queryset according to the user's data scope.
    """

    if not user or not user.is_authenticated:
        return queryset.none()

    if user.is_superuser:
        return queryset

    scope = get_permission_scope(
        user,
        permission_codename,
    )

    employee = get_user_employee(user)

    if not scope:
        return queryset.none()

    if scope in ["GLOBAL", "ORGANIZATION", "COMPANY"]:
        return queryset

    if not employee:
        return queryset.none()

    if scope == "OWN":
        return queryset.filter(id=employee.id)

    if scope == "TEAM":
        return queryset.filter(
            Q(id=employee.id)
            | Q(manager=employee)
        )

    if scope == "DEPARTMENT":
        if not employee.department_id:
            return queryset.none()

        return queryset.filter(
            department_id=employee.department_id
        )

    if scope == "BRANCH":
        if not employee.branch_id:
            return queryset.none()

        return queryset.filter(
            branch_id=employee.branch_id
        )

    return queryset.none()


def scope_related_employee_queryset(
    user,
    queryset,
    employee_field="employee",
    permission_codename=None,
):
    """
    Scope querysets that contain an Employee relation.

    Examples:
        AttendanceRecord -> employee
        LeaveRequest -> employee
        Payslip -> employee
        EmployeeDocument -> employee
    """

    if not user or not user.is_authenticated:
        return queryset.none()

    if user.is_superuser:
        return queryset

    if not permission_codename:
        return queryset.none()

    scope = get_permission_scope(
        user,
        permission_codename,
    )

    employee = get_user_employee(user)

    if not scope:
        return queryset.none()

    if scope in ["GLOBAL", "ORGANIZATION", "COMPANY"]:
        return queryset

    if not employee:
        return queryset.none()

    if scope == "OWN":
        return queryset.filter(
            **{f"{employee_field}_id": employee.id}
        )

    if scope == "TEAM":
        return queryset.filter(
            Q(**{f"{employee_field}_id": employee.id})
            | Q(**{f"{employee_field}__manager_id": employee.id})
        )

    if scope == "DEPARTMENT":
        if not employee.department_id:
            return queryset.none()

        return queryset.filter(
            **{
                f"{employee_field}__department_id":
                    employee.department_id
            }
        )

    if scope == "BRANCH":
        if not employee.branch_id:
            return queryset.none()

        return queryset.filter(
            **{
                f"{employee_field}__branch_id":
                    employee.branch_id
            }
        )

    return queryset.none()