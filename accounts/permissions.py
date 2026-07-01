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