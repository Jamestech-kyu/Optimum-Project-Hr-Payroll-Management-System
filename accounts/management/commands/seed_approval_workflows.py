from django.core.management.base import BaseCommand
from accounts.models import (
    Role,
    Permission,
    ApprovalWorkflow,
    ApprovalStep,
)


class Command(BaseCommand):
    help = "Seed approval workflows"

    def handle(self, *args, **kwargs):
        workflows = [
            {
                "name": "Leave Approval Workflow",
                "module": "LEAVE",
                "steps": [
                    ("MANAGER", "leave.approve"),
                    ("HR", "leave.approve"),
                ],
            },
            {
                "name": "Payroll Approval Workflow",
                "module": "PAYROLL",
                "steps": [
                    ("PAYROLL_OFFICER", "payroll.generate"),
                    ("ADMIN", "payroll.approve"),
                ],
            },
        ]

        for workflow_data in workflows:
            workflow, _ = ApprovalWorkflow.objects.get_or_create(
                name=workflow_data["name"],
                module=workflow_data["module"],
            )

            for index, (role_name, permission_code) in enumerate(
                workflow_data["steps"],
                start=1,
            ):
                role = Role.objects.filter(name=role_name).first()
                permission = Permission.objects.filter(codename=permission_code).first()

                if role:
                    ApprovalStep.objects.get_or_create(
                        workflow=workflow,
                        step_order=index,
                        defaults={
                            "role": role,
                            "permission_required": permission,
                        },
                    )

        self.stdout.write(self.style.SUCCESS("Approval workflows seeded successfully."))