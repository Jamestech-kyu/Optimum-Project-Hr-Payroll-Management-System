from django.core.management.base import BaseCommand
from accounts.models import Role, Permission, RolePermission


class Command(BaseCommand):
    help = "Seed default permissions and assign them to roles"

    def handle(self, *args, **kwargs):
        permissions = [
            ("ACCOUNTS", "accounts.manage", "Manage Accounts"),
            ("EMPLOYEES", "employees.view", "View Employees"),
            ("EMPLOYEES", "employees.create", "Create Employees"),
            ("EMPLOYEES", "employees.update", "Update Employees"),
            ("EMPLOYEES", "employees.delete", "Delete Employees"),
            ("ATTENDANCE", "attendance.view", "View Attendance"),
            ("ATTENDANCE", "attendance.manage", "Manage Attendance"),
            ("LEAVE", "leave.view", "View Leave"),
            ("LEAVE", "leave.request", "Request Leave"),
            ("LEAVE", "leave.approve", "Approve Leave"),
            ("PAYROLL", "payroll.view", "View Payroll"),
            ("PAYROLL", "payroll.generate", "Generate Payroll"),
            ("PAYROLL", "payroll.approve", "Approve Payroll"),
            ("REPORTS", "reports.view", "View Reports"),
            ("AUDIT", "audit.view", "View Audit Logs"),
            ("SETTINGS", "settings.manage", "Manage Settings"),
        ]

        for module, codename, name in permissions:
            Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "module": module,
                    "name": name,
                },
            )

        role_permissions = {
            "SUPER_ADMIN": [p[1] for p in permissions],
            "ADMIN": [
                "accounts.manage",
                "employees.view", "employees.create", "employees.update",
                "attendance.view", "attendance.manage",
                "leave.view", "leave.approve",
                "payroll.view", "reports.view",
                "settings.manage",
            ],
            "HR": [
                "employees.view", "employees.create", "employees.update",
                "attendance.view", "attendance.manage",
                "leave.view", "leave.approve",
                "reports.view",
            ],
            "MANAGER": [
                "employees.view",
                "attendance.view",
                "leave.view", "leave.approve",
                "reports.view",
            ],
            "PAYROLL_OFFICER": [
                "employees.view",
                "attendance.view",
                "leave.view",
                "payroll.view", "payroll.generate",
                "reports.view",
            ],
            "EMPLOYEE": [
                "leave.request",
                "leave.view",
                "attendance.view",
            ],
        }

        for role_name, codenames in role_permissions.items():
            role = Role.objects.filter(name=role_name).first()
            if not role:
                self.stdout.write(self.style.WARNING(f"Role not found: {role_name}"))
                continue

            for codename in codenames:
                permission = Permission.objects.get(codename=codename)
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                )

        self.stdout.write(self.style.SUCCESS("Permissions seeded successfully."))