from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name == "SUPER_ADMIN"
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name == "ADMIN"
        )


class IsHR(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name == "HR"
        )


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name == "MANAGER"
        )


class IsPayrollOfficer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name == "PAYROLL_OFFICER"
        )


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name == "EMPLOYEE"
        )


class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name in ["ADMIN", "SUPER_ADMIN"]
        )


class IsHRorAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name in ["HR", "ADMIN", "SUPER_ADMIN"]
        )


class IsPayrollTeam(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.name in ["PAYROLL_OFFICER", "ADMIN", "SUPER_ADMIN"]
        )


class HasRolePermission(BasePermission):
    def __init__(self, required_permission):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if not user.role:
            return False

        return user.role.role_permissions.filter(
            permission__codename=self.required_permission
        ).exists()


from rest_framework.permissions import BasePermission
from .services import user_has_permission


def RequiredPermission(permission_codename):
    class PermissionChecker(BasePermission):
        def has_permission(self, request, view):
            return user_has_permission(
                request.user,
                permission_codename,
            )

    return PermissionChecker