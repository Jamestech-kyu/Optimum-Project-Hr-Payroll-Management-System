from django.core.management.base import BaseCommand
from accounts.models import (
    Role,
    Permission,
    PermissionGroup,
    GroupPermission,
    RolePermissionGroup,
)


class Command(BaseCommand):
    help = "Seed permission groups and assign groups to roles"

    def handle(self, *args, **kwargs):
        groups = {
            "Employee Management": [
                "employees.view",
                "employees.create",
                "employees.update",
                "employees.delete",
            ],
            "Attendance Administration": [
                "attendance.view",
                "attendance.manage",
            ],
            "Leave Administration": [
                "leave.view",
                "leave.approve",
            ],
            "Payroll Administration": [
                "payroll.view",
                "payroll.generate",
                "payroll.approve",
            ],
            "Reports": [
                "reports.view",
            ],
            "Audit": [
                "audit.view",
            ],
            "Settings": [
                "settings.manage",
            ],
            "Accounts Administration": [
                "accounts.manage",
            ],
            "Employee Self Service": [
                "leave.request",
                "leave.view",
                "attendance.view",
            ],
        }

        for group_name, permission_codes in groups.items():
            group, _ = PermissionGroup.objects.get_or_create(
                name=group_name,
                defaults={"description": f"{group_name} permissions"},
            )

            for code in permission_codes:
                permission = Permission.objects.filter(codename=code).first()
                if permission:
                    GroupPermission.objects.get_or_create(
                        group=group,
                        permission=permission,
                    )

        role_groups = {
            "SUPER_ADMIN": [
                "Accounts Administration",
                "Employee Management",
                "Attendance Administration",
                "Leave Administration",
                "Payroll Administration",
                "Reports",
                "Audit",
                "Settings",
            ],
            "ADMIN": [
                "Accounts Administration",
                "Employee Management",
                "Attendance Administration",
                "Leave Administration",
                "Reports",
                "Settings",
            ],
            "HR": [
                "Employee Management",
                "Attendance Administration",
                "Leave Administration",
                "Reports",
            ],
            "MANAGER": [
                "Attendance Administration",
                "Leave Administration",
                "Reports",
            ],
            "PAYROLL_OFFICER": [
                "Payroll Administration",
                "Reports",
            ],
            "EMPLOYEE": [
                "Employee Self Service",
            ],
        }

        for role_name, group_names in role_groups.items():
            role = Role.objects.filter(name=role_name).first()

            if not role:
                self.stdout.write(self.style.WARNING(f"Role not found: {role_name}"))
                continue

            for group_name in group_names:
                group = PermissionGroup.objects.filter(name=group_name).first()

                if group:
                    RolePermissionGroup.objects.get_or_create(
                        role=role,
                        group=group,
                    )

        self.stdout.write(self.style.SUCCESS("Permission groups seeded successfully."))