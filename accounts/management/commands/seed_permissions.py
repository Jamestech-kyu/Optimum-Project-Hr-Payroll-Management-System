from django.core.management.base import BaseCommand

from accounts.models import Permission, Role, RolePermission


class Command(BaseCommand):
    help = "Seed default permissions and assign them to roles"

    def handle(self, *args, **kwargs):
        permissions = [
            ("ACCOUNTS", "accounts.manage", "Manage Accounts"),
            ("EMPLOYEES", "employees.view", "View Employees"),
            ("EMPLOYEES", "employees.create", "Create Employees"),
            ("EMPLOYEES", "employees.update", "Update Employees"),
            ("EMPLOYEES", "employees.delete", "Delete Employees"),
            ("EMPLOYEES", "salary.view", "View Salary Information"),
            ("EMPLOYEES", "salary.adjust", "Adjust Employee Salary"),
            ("ATTENDANCE", "attendance.view", "View Attendance"),
            ("ATTENDANCE", "attendance.manage", "Manage Attendance"),
            ("LEAVE", "leave.view", "View Leave"),
            ("LEAVE", "leave.request", "Request Leave"),
            ("LEAVE", "leave.approve", "Approve Leave"),
            ("PAYROLL", "payroll.view", "View Payroll"),
            ("PAYROLL", "payroll.generate", "Generate Payroll"),
            ("PAYROLL", "payroll.approve", "Approve Payroll"),
            ("BENEFITS", "benefits.view", "View Benefits"),
            ("BENEFITS", "benefits.create", "Create Benefits"),
            ("BENEFITS", "benefits.update", "Update Benefits"),
            ("BENEFITS", "benefits.delete", "Delete Benefits"),
            ("BENEFITS", "benefits.enroll", "Enroll Benefits"),
            ("BENEFITS", "benefits.approve", "Approve Benefits"),
            ("PERFORMANCE", "performance.view", "View Performance"),
            ("PERFORMANCE", "performance.create", "Create Performance"),
            ("PERFORMANCE", "performance.update", "Update Performance"),
            ("PERFORMANCE", "performance.delete", "Delete Performance"),
            (
                "PERFORMANCE",
                "performance.update_progress",
                "Update Performance Progress",
            ),
            (
                "PERFORMANCE",
                "performance.submit_review",
                "Submit Performance Review",
            ),
            (
                "PERFORMANCE",
                "performance.manager_approve",
                "Manager Approve Performance Review",
            ),
            (
                "PERFORMANCE",
                "performance.hr_approve",
                "HR Approve Performance Review",
            ),
            (
                "PERFORMANCE",
                "performance.finalize",
                "Finalize Performance Review",
            ),
            ("TRAINING", "training.view", "View Training"),
            ("TRAINING", "training.create", "Create Training"),
            ("TRAINING", "training.update", "Update Training"),
            ("TRAINING", "training.delete", "Delete Training"),
            ("TRAINING", "training.enroll", "Enroll Training"),
            ("TRAINING", "training.approve", "Approve Training"),
            ("TRAINING", "training.reject", "Reject Training"),
            ("TRAINING", "training.attendance", "Record Training Attendance"),
            ("TRAINING", "training.assessment", "Record Training Assessment"),
            ("TRAINING", "training.recommend", "Recommend Training"),
            ("CONTRACTS", "contracts.view", "View Contracts"),
            ("CONTRACTS", "contracts.create", "Create Contracts"),
            ("CONTRACTS", "contracts.update", "Update Contracts"),
            ("CONTRACTS", "contracts.approve", "Approve Contracts"),
            ("CONTRACTS", "contracts.renew", "Renew Contracts"),
            ("CONTRACTS", "contracts.terminate", "Terminate Contracts"),
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

        all_training_permissions = [
            "training.view",
            "training.create",
            "training.update",
            "training.delete",
            "training.enroll",
            "training.approve",
            "training.reject",
            "training.attendance",
            "training.assessment",
            "training.recommend",
        ]

        all_contract_permissions = [
            "contracts.view",
            "contracts.create",
            "contracts.update",
            "contracts.approve",
            "contracts.renew",
            "contracts.terminate",
        ]

        role_permissions = {
            "SUPER_ADMIN": [p[1] for p in permissions],
            "ADMIN": [
                "accounts.manage",
                "employees.view", "employees.create", "employees.update",
                "employees.delete",
                "salary.view", "salary.adjust",
                "attendance.view", "attendance.manage",
                "leave.view", "leave.approve",
                "benefits.view", "benefits.create",
                "benefits.update", "benefits.delete",
                "benefits.enroll", "benefits.approve",
                "performance.view", "performance.create",
                "performance.update", "performance.delete",
                "performance.update_progress",
                "performance.submit_review",
                "performance.manager_approve",
                "performance.hr_approve",
                "performance.finalize",
                *all_training_permissions,
                *all_contract_permissions,
                "payroll.view", "payroll.generate", "payroll.approve",
                "reports.view",
                "settings.manage",
            ],
            "HR": [
                "employees.view", "employees.create", "employees.update",
                "employees.delete",
                "salary.view", "salary.adjust",
                "attendance.view", "attendance.manage",
                "leave.view", "leave.approve",
                "benefits.view", "benefits.create",
                "benefits.update", "benefits.delete",
                "benefits.enroll", "benefits.approve",
                "performance.view", "performance.create",
                "performance.update",
                "performance.submit_review",
                "performance.hr_approve",
                "performance.finalize",
                *all_training_permissions,
                *all_contract_permissions,
                "payroll.view",
                "reports.view",
            ],
            "MANAGER": [
                "employees.view",
                "salary.view",
                "benefits.view",
                "contracts.view",
                "payroll.view", "payroll.approve",
                "performance.view",
                "performance.create",
                "performance.update",
                "performance.submit_review",
                "performance.manager_approve",
                "performance.update_progress",
                "training.view",
                "training.enroll",
                "training.attendance",
                "training.recommend",
                "attendance.view",
                "leave.view", "leave.approve",
                "reports.view",
            ],
            "PAYROLL_OFFICER": [
                "employees.view",
                "salary.view",
                "benefits.view",
                "attendance.view",
                "leave.view",
                "contracts.view",
                "payroll.view", "payroll.generate",
                "reports.view",
            ],
            # Read-only company-wide oversight; the client ships an executive
            # dashboard for this role.
            "EXECUTIVE": [
                "employees.view",
                "salary.view",
                "attendance.view",
                "leave.view",
                "benefits.view",
                "performance.view",
                "training.view",
                "payroll.view",
                "contracts.view",
                "reports.view",
                "audit.view",
            ],
            "DEPARTMENT_HEAD": [
                "employees.view",
                "attendance.view",
                "leave.view", "leave.approve",
                "benefits.view",
                "performance.view", "performance.create",
                "performance.update",
                "performance.submit_review",
                "performance.manager_approve",
                "performance.update_progress",
                "training.view", "training.enroll",
                "training.attendance", "training.recommend",
                "contracts.view",
                "reports.view",
            ],
            "FINANCE": [
                "employees.view",
                "salary.view", "salary.adjust",
                "benefits.view", "benefits.approve",
                "payroll.view", "payroll.generate", "payroll.approve",
                "contracts.view",
                "reports.view",
            ],
            "EMPLOYEE": [
                "leave.request",
                "leave.view",
                "attendance.view",
                "employees.view",
                "salary.view",
                "benefits.view",
                "contracts.view",
                # At OWN scope this exposes only the employee's own payslips.
                "payroll.view",
                "performance.view",
                "performance.update_progress",
                "training.view",
            ],
        }

        # How much data each role may see. RolePermission.data_scope defaults to
        # "OWN", which resolves to an empty queryset for any user without a
        # linked employee profile, so every role must state its scope explicitly
        # or administrative roles silently see nothing at all.
        role_scopes = {
            "SUPER_ADMIN": "ORGANIZATION",
            "ADMIN": "ORGANIZATION",
            "EXECUTIVE": "ORGANIZATION",
            "HR": "ORGANIZATION",
            "FINANCE": "ORGANIZATION",
            "PAYROLL_OFFICER": "ORGANIZATION",
            "DEPARTMENT_HEAD": "DEPARTMENT",
            "MANAGER": "DEPARTMENT",
            "EMPLOYEE": "OWN",
        }

        # Self-service permissions stay scoped to the holder's own records even
        # for senior roles, so a manager cannot approve their own leave.
        own_scoped_codenames = {"leave.request"}

        for role_name, codenames in role_permissions.items():
            role = Role.objects.filter(name=role_name).first()
            if not role:
                self.stdout.write(
                    self.style.WARNING(f"Role not found: {role_name}")
                )
                continue

            role_scope = role_scopes.get(role_name, "OWN")

            for codename in codenames:
                permission = Permission.objects.get(codename=codename)
                scope = (
                    "OWN"
                    if codename in own_scoped_codenames
                    else role_scope
                )
                RolePermission.objects.update_or_create(
                    role=role,
                    permission=permission,
                    defaults={"data_scope": scope},
                )

            # Rows granted outside this command (earlier seeds, manual edits)
            # would otherwise keep the "OWN" default and silently resolve to an
            # empty queryset. Align their scope too and report them, rather than
            # deleting grants this command did not create.
            stale = RolePermission.objects.filter(role=role).exclude(
                permission__codename__in=codenames
            ).exclude(
                permission__codename__in=own_scoped_codenames
            )

            stale_codenames = sorted(
                row.permission.codename for row in stale.select_related("permission")
            )

            if stale_codenames:
                stale.update(data_scope=role_scope)

            self.stdout.write(
                f"  {role_name}: {len(codenames)} permissions at {role_scope} scope"
            )

            if stale_codenames:
                self.stdout.write(
                    self.style.WARNING(
                        f"    {len(stale_codenames)} extra grant(s) not declared here, "
                        f"rescoped to {role_scope}: {', '.join(stale_codenames)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS("Permissions seeded successfully.")
        )
